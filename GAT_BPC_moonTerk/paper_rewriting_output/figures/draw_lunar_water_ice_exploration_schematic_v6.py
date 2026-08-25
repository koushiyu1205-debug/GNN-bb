#!/usr/bin/env python3
"""Add a 200 km regional context below the four-layer lunar stack.

The regional LOLA hillshade is centered on the same location as the 50 km
mission instance.  The local 50 km footprint is therefore shown at its true
one-quarter edge scale, rather than being stretched to match the context map.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(FIGURE_DIR))

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np

import draw_lunar_water_ice_exploration_schematic_v5 as v5
from draw_lunar_real_environment_task_sites import _build_official_lola_hillshade_rgb
from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


INSTANCE_PATH = ROOT / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
RAW_MAP_DIR = ROOT / "data/raw_maps"
REAL_ENVIRONMENT_REFERENCE = (
    ROOT / "output/data_figures/lunar_sp50_020_instance_001_real_environment.png"
)
OUTPUT_PATH = FIGURE_DIR / "lunar_water_ice_exploration_schematic_v6.png"

REGIONAL_EXTENT_KM = 200.0
LOCAL_EXTENT_KM = 50.0
REGIONAL_MIN_KM = -(REGIONAL_EXTENT_KM - LOCAL_EXTENT_KM) / 2.0
REGIONAL_MAX_KM = LOCAL_EXTENT_KM + (REGIONAL_EXTENT_KM - LOCAL_EXTENT_KM) / 2.0
LOCAL_DISPLAY_SCALE = 1.65
LOCAL_DISPLAY_MIN_KM = 0.5 * LOCAL_EXTENT_KM * (1.0 - LOCAL_DISPLAY_SCALE)
LOCAL_DISPLAY_MAX_KM = LOCAL_EXTENT_KM - LOCAL_DISPLAY_MIN_KM

LAYER_Z = {
    "regional": 0.0,
    "terrain": 13.0,
    "risk": 25.0,
    "illumination": 37.0,
    "routes": 49.0,
}


def main() -> int:
    if not REAL_ENVIRONMENT_REFERENCE.is_file():
        raise FileNotFoundError(
            "real-environment style reference is unavailable: "
            f"{REAL_ENVIRONMENT_REFERENCE}"
        )

    instance = read_json(INSTANCE_PATH)
    resource_map = instance["resource_map"]
    center_x_km = float(resource_map["center_x_km"])
    center_y_km = float(resource_map["center_y_km"])
    local_extent_km = float(resource_map["extent_km"])
    if abs(local_extent_km - LOCAL_EXTENT_KM) > 1.0e-9:
        raise ValueError(
            f"expected a {LOCAL_EXTENT_KM:g} km local instance, found {local_extent_km:g}"
        )

    local_context = _build_context(
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=LOCAL_EXTENT_KM,
        output_cells=800,
    )
    regional_context = _build_context(
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=REGIONAL_EXTENT_KM,
        output_cells=1000,
    )
    regional_rgba = _build_official_lola_hillshade_rgb(
        official_hillshade=np.asarray(
            regional_context["surfaces"]["hillshade"],
            dtype="float64",
        )
    )
    local_rgba, layer_mappables = v5._build_environment_layers(
        local_context,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=LOCAL_EXTENT_KM,
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
    if len(selected_task_ids) != 6:
        raise ValueError(
            f"expected six sparse representative tasks, found {len(selected_task_ids)}"
        )
    display_instance, display_edge_lookup, display_trips = _build_enlarged_route_inputs(
        instance=instance,
        edge_lookup=edge_lookup,
        trips=trips,
    )

    # Reuse the v5 route and layer functions with the local planes shifted up.
    v5.LAYER_Z.clear()
    v5.LAYER_Z.update(
        {
            "terrain": LAYER_Z["terrain"],
            "risk": LAYER_Z["risk"],
            "illumination": LAYER_Z["illumination"],
            "routes": LAYER_Z["routes"],
        }
    )

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    stack_ax = fig.add_axes(
        (0.005, 0.025, 0.785, 0.945),
        projection="3d",
        computed_zorder=False,
    )
    key_ax = fig.add_axes((0.790, 0.065, 0.195, 0.86))

    _draw_regional_plane(
        stack_ax,
        regional_rgba,
        z=LAYER_Z["regional"],
    )
    _draw_local_footprint_on_regional_plane(stack_ax)
    _draw_local_environment_stack(
        stack_ax,
        local_rgba,
    )
    _draw_regional_to_local_guides(stack_ax)
    v5._draw_route_layer(
        stack_ax,
        instance=display_instance,
        edge_lookup=display_edge_lookup,
        trips=display_trips,
        selected_task_ids=selected_task_ids,
    )
    _format_stack_axis(stack_ax)
    _draw_key_panel(
        key_ax,
        layer_mappables=layer_mappables,
        selected_task_count=len(selected_task_ids),
    )

    instance_id = str(instance.get("instance_id", INSTANCE_PATH.stem))
    layer_sources = {
        key: Path(value["source"]).name
        for key, value in (regional_context.get("layer_status") or {}).items()
        if isinstance(value, dict)
        and value.get("status") == "ready"
        and value.get("source")
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT_PATH,
        bbox_inches="tight",
        pad_inches=0.045,
        facecolor="white",
        metadata={
            "Title": "Regional-to-local pseudo-3D lunar planning layers",
            "Description": (
                f"Instance={instance_id}; bottom-to-top layers=200 km by 200 km "
                "regional LOLA hillshade, 50 km by 50 km local terrain, deterministic "
                "traversal risk, average solar visibility, and sparse logical routes; "
                "the local footprint is centered and displayed at true 1:4 edge scale "
                "on the regional plane; the four local layers are enlarged by 1.65 for "
                "legibility and linked to that footprint by registration guides; the "
                "regional layer follows the style "
                "of lunar_sp50_020_instance_001_real_environment without task or depot "
                "markers; the route layer contains one depot and six representative tasks; "
                "V1 has two closed depot-to-depot trips and V2 has one; reference routes "
                "are feasible but reference_exact_status=NOT_SOLVED; "
                f"sources={layer_sources}"
            ),
            "Software": "lunar-ice-bpc deterministic Matplotlib 3D renderer",
        },
    )
    plt.close(fig)

    print(f"wrote {OUTPUT_PATH}")
    print(f"real_environment_reference={REAL_ENVIRONMENT_REFERENCE}")
    print(f"instance_id={instance_id}")
    print(
        "regional_extent_km=200 local_extent_km=50 "
        "local_bounds_in_regional_coordinates=[0,50]x[0,50]"
    )
    print("local_display_scale=1.65 (presentation only)")
    print(f"representative_task_count={len(selected_task_ids)}")
    for trip in trips:
        print(
            f"{trip['vehicle']} trip_{trip['trip']} "
            f"tasks={','.join(trip['task_ids'])} "
            f"closed={trip['closed']} feasible={trip['feasible']}"
        )
    print("layer_order=regional_context,terrain,risk,illumination,logical_routes")
    print("reference_exact_status=NOT_SOLVED; figure does not claim optimality")
    return 0


def _build_context(
    *,
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
    output_cells: int,
) -> dict[str, Any]:
    context = build_real_map_surface_context(
        raw_map_dir=RAW_MAP_DIR,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=output_cells,
        allow_remote=False,
        allow_partial=False,
    )
    if context.get("status") != "REAL_MAP_SURFACES_READY":
        raise RuntimeError(
            f"real lunar layers unavailable for extent={extent_km:g} km: "
            f"{context.get('status')}"
        )
    return context


def _draw_regional_plane(
    ax: plt.Axes,
    rgba: np.ndarray,
    *,
    z: float,
) -> None:
    step = max(1, int(np.ceil(rgba.shape[0] / 260.0)))
    display_rgba = np.asarray(rgba[::step, ::step, :], dtype="float64")
    y = np.linspace(REGIONAL_MIN_KM, REGIONAL_MAX_KM, display_rgba.shape[0])
    x = np.linspace(REGIONAL_MIN_KM, REGIONAL_MAX_KM, display_rgba.shape[1])
    x_grid, y_grid = np.meshgrid(x, y)
    z_grid = np.full_like(x_grid, z)
    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        rstride=1,
        cstride=1,
        facecolors=display_rgba,
        shade=False,
        antialiased=False,
        linewidth=0.0,
        zorder=0.5,
    )
    edge_color = "#303A40"
    for x_values, y_values in (
        ((REGIONAL_MIN_KM, REGIONAL_MAX_KM), (REGIONAL_MIN_KM, REGIONAL_MIN_KM)),
        ((REGIONAL_MAX_KM, REGIONAL_MAX_KM), (REGIONAL_MIN_KM, REGIONAL_MAX_KM)),
        ((REGIONAL_MAX_KM, REGIONAL_MIN_KM), (REGIONAL_MAX_KM, REGIONAL_MAX_KM)),
        ((REGIONAL_MIN_KM, REGIONAL_MIN_KM), (REGIONAL_MAX_KM, REGIONAL_MIN_KM)),
    ):
        ax.plot(
            x_values,
            y_values,
            [z, z],
            color=edge_color,
            linewidth=0.85,
            alpha=0.88,
            zorder=0.6,
        )


def _draw_local_footprint_on_regional_plane(ax: plt.Axes) -> None:
    z = LAYER_Z["regional"] + 0.45
    color = "#00A2A8"
    corners = np.asarray(
        (
            (0.0, 0.0),
            (LOCAL_EXTENT_KM, 0.0),
            (LOCAL_EXTENT_KM, LOCAL_EXTENT_KM),
            (0.0, LOCAL_EXTENT_KM),
            (0.0, 0.0),
        ),
        dtype="float64",
    )
    ax.plot(
        corners[:, 0],
        corners[:, 1],
        np.full(corners.shape[0], z),
        color="white",
        linewidth=3.1,
        solid_capstyle="round",
        zorder=0.8,
    )
    ax.plot(
        corners[:, 0],
        corners[:, 1],
        np.full(corners.shape[0], z + 0.03),
        color=color,
        linewidth=1.55,
        linestyle=(0, (4.0, 2.2)),
        solid_capstyle="round",
        zorder=0.9,
    )


def _draw_local_environment_stack(
    ax: plt.Axes,
    rgba_layers: dict[str, np.ndarray],
) -> None:
    for key in ("terrain", "risk", "illumination"):
        _plot_local_plane(
            ax,
            rgba_layers[key],
            z=LAYER_Z[key],
        )

    route_rgba = np.ones((120, 120, 4), dtype="float64")
    route_rgba[..., :3] = np.asarray((0.90, 0.93, 0.94), dtype="float64")
    route_rgba[..., 3] = 0.55
    _plot_local_plane(
        ax,
        route_rgba,
        z=LAYER_Z["routes"],
    )

    for x, y in (
        (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MIN_KM),
        (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MIN_KM),
        (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MAX_KM),
        (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM),
    ):
        ax.plot(
            [x, x],
            [y, y],
            [LAYER_Z["terrain"], LAYER_Z["routes"]],
            color="#7C868C",
            linewidth=0.65,
            linestyle=(0, (1.5, 3.0)),
            alpha=0.55,
            zorder=1.6,
        )


def _plot_local_plane(
    ax: plt.Axes,
    rgba: np.ndarray,
    *,
    z: float,
) -> None:
    step = max(1, int(np.ceil(rgba.shape[0] / 220.0)))
    display_rgba = np.asarray(rgba[::step, ::step, :], dtype="float64")
    y = np.linspace(LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM, display_rgba.shape[0])
    x = np.linspace(LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM, display_rgba.shape[1])
    x_grid, y_grid = np.meshgrid(x, y)
    z_grid = np.full_like(x_grid, z)
    surface_zorder = 1.0 + z / 12.0
    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        rstride=1,
        cstride=1,
        facecolors=display_rgba,
        shade=False,
        antialiased=False,
        linewidth=0.0,
        zorder=surface_zorder,
    )
    edge_color = "#313A40"
    for x_values, y_values in (
        ((LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM), (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MIN_KM)),
        ((LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MAX_KM), (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM)),
        ((LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MIN_KM), (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MAX_KM)),
        ((LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MIN_KM), (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MIN_KM)),
    ):
        ax.plot(
            x_values,
            y_values,
            [z, z],
            color=edge_color,
            linewidth=0.85,
            alpha=0.82,
            zorder=surface_zorder + 0.1,
        )


def _draw_regional_to_local_guides(ax: plt.Axes) -> None:
    regional_corners = (
        (0.0, 0.0),
        (LOCAL_EXTENT_KM, 0.0),
        (LOCAL_EXTENT_KM, LOCAL_EXTENT_KM),
        (0.0, LOCAL_EXTENT_KM),
    )
    display_corners = (
        (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MIN_KM),
        (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MIN_KM),
        (LOCAL_DISPLAY_MAX_KM, LOCAL_DISPLAY_MAX_KM),
        (LOCAL_DISPLAY_MIN_KM, LOCAL_DISPLAY_MAX_KM),
    )
    for (regional_x, regional_y), (display_x, display_y) in zip(
        regional_corners,
        display_corners,
    ):
        ax.plot(
            [regional_x, display_x],
            [regional_y, display_y],
            [LAYER_Z["regional"], LAYER_Z["terrain"]],
            color="#00A2A8",
            linewidth=0.75,
            linestyle=(0, (1.5, 3.0)),
            alpha=0.72,
            zorder=1.5,
        )


def _build_enlarged_route_inputs(
    *,
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    trips: list[dict[str, Any]],
) -> tuple[
    dict[str, Any],
    dict[tuple[str, str, str], dict[str, Any]],
    list[dict[str, Any]],
]:
    display_instance = deepcopy(instance)
    display_instance["depot"]["xy_km"] = _enlarge_xy(
        display_instance["depot"]["xy_km"]
    ).tolist()
    for task in display_instance["tasks"].values():
        task["xy_km"] = _enlarge_xy(task["xy_km"]).tolist()

    display_edge_lookup = deepcopy(edge_lookup)
    for option in display_edge_lookup.values():
        option["path_xy"] = _enlarge_xy(option["path_xy"]).tolist()

    display_trips = deepcopy(trips)
    for trip in display_trips:
        for leg_item in trip["legs"]:
            leg_item["points"] = _enlarge_xy(leg_item["points"])
    return display_instance, display_edge_lookup, display_trips


def _enlarge_xy(values: Any) -> np.ndarray:
    matrix = np.asarray(values, dtype="float64")
    return LOCAL_DISPLAY_MIN_KM + LOCAL_DISPLAY_SCALE * matrix


def _format_stack_axis(ax: plt.Axes) -> None:
    ax.set_xlim(REGIONAL_MIN_KM - 4.0, REGIONAL_MAX_KM + 4.0)
    ax.set_ylim(REGIONAL_MIN_KM - 4.0, REGIONAL_MAX_KM + 4.0)
    ax.set_zlim(-2.0, LAYER_Z["routes"] + 12.0)
    ax.set_box_aspect((1.08, 1.08, 0.62))
    ax.view_init(elev=28.0, azim=-57.0)
    ax.set_proj_type("persp", focal_length=0.90)
    ax.set_axis_off()
    ax.text2D(
        0.035,
        0.965,
        "Regional-to-local lunar environment and routing layers",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12.0,
        fontweight="semibold",
        color="#172027",
    )
    ax.text2D(
        0.037,
        0.925,
        "A 50 km × 50 km mission region nested within a 200 km × 200 km LOLA context; local layers enlarged for legibility",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.7,
        color="#5A656C",
    )


def _draw_key_panel(
    ax: plt.Axes,
    *,
    layer_mappables: dict[str, mpl.cm.ScalarMappable],
    selected_task_count: int,
) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    ax.text(0.03, 0.970, "Layer order", fontsize=9.5, fontweight="semibold", color="#172027")
    layer_rows = (
        (0.895, "5", "Logical routes", "#EDF2F4"),
        (0.830, "4", "Illumination", "#6F929D"),
        (0.765, "3", "Traversal risk", "#C15C70"),
        (0.700, "2", "Local terrain (50 km)", "#7FAE92"),
        (0.635, "1", "Regional context (200 km)", "#AEB5B9"),
    )
    for y, number, label, color in layer_rows:
        ax.add_patch(
            Rectangle(
                (0.07, y),
                0.25,
                0.044,
                facecolor=color,
                edgecolor="#364047",
                linewidth=0.65,
            )
        )
        ax.text(0.195, y + 0.022, number, ha="center", va="center", fontsize=6.8, fontweight="bold", color="#172027")
        ax.text(0.37, y + 0.022, label, ha="left", va="center", fontsize=7.1, color="#28343B")
    ax.add_patch(
        FancyArrowPatch(
            (0.035, 0.640),
            (0.035, 0.938),
            arrowstyle="-|>",
            mutation_scale=9.0,
            linewidth=0.8,
            color="#667178",
        )
    )

    ax.text(0.05, 0.582, "spatial relation", fontsize=6.6, color="#39444A")
    ax.add_patch(Rectangle((0.08, 0.515), 0.31, 0.060, facecolor="#E2E5E7", edgecolor="#505A60", linewidth=0.6))
    ax.add_patch(Rectangle((0.198, 0.530), 0.078, 0.030, facecolor="none", edgecolor="#00A2A8", linewidth=1.1, linestyle=(0, (3.0, 1.8))))
    ax.text(0.44, 0.557, "centered 50 km footprint", fontsize=6.4, color="#39444A", va="center")
    ax.text(0.44, 0.532, "upper layers enlarged 1.65×", fontsize=6.1, color="#5A656C", va="center")

    _draw_gradient_key(
        ax,
        mappable=layer_mappables["illumination"],
        y=0.456,
        label="solar visibility index",
        low="0",
        high="1",
    )
    _draw_gradient_key(
        ax,
        mappable=layer_mappables["risk"],
        y=0.380,
        label="risk index",
        low="0.1",
        high="0.9",
    )

    ax.plot([0.03, 0.97], [0.330, 0.330], color="#D0D5D8", linewidth=0.7)
    ax.text(0.03, 0.303, "Sparse routing layer", fontsize=8.8, fontweight="semibold", color="#172027")
    ax.text(0.03, 0.270, f"{selected_task_count} tasks; 2 vehicles; 3 closed trips", fontsize=6.7, color="#5A656C")

    task_rows = (
        ("detect", "detection"),
        ("sample", "sampling"),
        ("drill", "drilling"),
    )
    for index, (mode, label) in enumerate(task_rows):
        y = 0.230 - 0.043 * index
        ax.scatter(
            [0.10],
            [y],
            s=45,
            marker=v5.TASK_MARKERS[mode],
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.8,
        )
        ax.text(0.19, y, label, fontsize=7.0, color="#28343B", va="center")
    ax.scatter([0.10], [0.101], s=86, marker="*", facecolor="white", edgecolor="#11181D", linewidth=0.9)
    ax.text(0.19, 0.101, "depot / recharge", fontsize=7.0, color="#28343B", va="center")

    ax.plot([0.49, 0.63], [0.230, 0.230], color=v5.VEHICLE_COLORS["V1"], linewidth=2.0)
    ax.text(0.67, 0.230, "V1: two trips", fontsize=6.7, color="#28343B", va="center")
    ax.plot([0.49, 0.63], [0.187, 0.187], color=v5.VEHICLE_COLORS["V2"], linewidth=2.0)
    ax.text(0.67, 0.187, "V2: one trip", fontsize=6.7, color="#28343B", va="center")
    ax.plot([0.49, 0.63], [0.144, 0.144], color="#4E5961", linewidth=1.6)
    ax.text(0.67, 0.144, "service", fontsize=6.6, color="#28343B", va="center")
    ax.plot([0.49, 0.63], [0.101, 0.101], color="#4E5961", linewidth=1.6, linestyle=(0, (5.0, 2.5)))
    ax.text(0.67, 0.101, "return", fontsize=6.6, color="#28343B", va="center")
    ax.plot([0.49, 0.63], [0.058, 0.058], color="#6F7A80", linewidth=1.5, linestyle=(0, (1.0, 2.0)))
    ax.text(0.67, 0.058, "alternative", fontsize=6.6, color="#28343B", va="center")

    ax.text(
        0.03,
        0.010,
        "Reference trips are feasible; no optimality claim is made.",
        fontsize=6.1,
        color="#5A656C",
    )


def _draw_gradient_key(
    ax: plt.Axes,
    *,
    mappable: mpl.cm.ScalarMappable,
    y: float,
    label: str,
    low: str,
    high: str,
) -> None:
    gradient = np.linspace(0.0, 1.0, 256)[None, :]
    rgba = mappable.cmap(gradient)
    ax.imshow(
        rgba,
        extent=(0.08, 0.90, y, y + 0.024),
        origin="lower",
        aspect="auto",
        interpolation="bilinear",
        zorder=1,
    )
    ax.add_patch(
        Rectangle(
            (0.08, y),
            0.82,
            0.024,
            facecolor="none",
            edgecolor="#4C565C",
            linewidth=0.55,
            zorder=2,
        )
    )
    ax.text(0.08, y + 0.032, label, fontsize=6.5, color="#39444A", ha="left", va="bottom")
    ax.text(0.08, y - 0.008, low, fontsize=6.0, color="#5A656C", ha="center", va="top")
    ax.text(0.90, y - 0.008, high, fontsize=6.0, color="#5A656C", ha="center", va="top")


if __name__ == "__main__":
    raise SystemExit(main())

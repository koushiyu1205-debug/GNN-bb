#!/usr/bin/env python3
"""Draw separated lunar environment layers and a fleet-routing panel.

The three environmental inputs are deliberately shown as independent maps.
The routing panel uses a neutral LOLA terrain background and contains all task,
fleet, candidate-path, and selected-trip annotations.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(FIGURE_DIR))

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from draw_lunar_instance_environment_panels import (
    _build_norm,
    _gaussian_smooth,
    _resolve_colormap,
)
from draw_lunar_real_environment_task_sites import _build_official_lola_hillshade_rgb
from draw_lunar_water_ice_exploration_schematic_v3 import (
    CANDIDATE_EDGE,
    TASK_MARKERS,
    TRIP_SPECS,
    VEHICLE_COLORS,
    _draw_candidate_alternatives,
    _draw_depot_and_fleet,
    _draw_task_sites,
    _draw_trip,
    _resolve_trip,
    _validate_candidate_edge,
)
from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


INSTANCE_PATH = ROOT / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
RAW_MAP_DIR = ROOT / "data/raw_maps"
OUTPUT_PATH = FIGURE_DIR / "lunar_water_ice_exploration_schematic_v4.png"


def main() -> int:
    instance = read_json(INSTANCE_PATH)
    resource_map = instance["resource_map"]
    extent_km = float(resource_map["extent_km"])
    context = build_real_map_surface_context(
        raw_map_dir=RAW_MAP_DIR,
        center_x_km=float(resource_map["center_x_km"]),
        center_y_km=float(resource_map["center_y_km"]),
        extent_km=extent_km,
        output_cells=1000,
        allow_remote=False,
        allow_partial=False,
    )
    if context.get("status") != "REAL_MAP_SURFACES_READY":
        raise RuntimeError(f"real lunar layers unavailable: {context.get('status')}")

    surfaces = context["surfaces"]
    terrain_rgba = _build_official_lola_hillshade_rgb(
        official_hillshade=np.asarray(surfaces["hillshade"], dtype="float64")
    )
    illumination = np.flipud(
        _gaussian_smooth(
            np.asarray(surfaces["illumination"], dtype="float64"),
            sigma_cells=4.0,
        )
    )
    traversal_risk = np.flipud(
        _gaussian_smooth(
            np.asarray(surfaces["risk"], dtype="float64"),
            sigma_cells=4.0,
        )
    )

    edge_lookup = {
        (str(edge["from"]), str(edge["to"]), str(option["path_type"])): option
        for edge in instance["logical_graph"]["edges"]
        for option in edge.get("path_options", [])
    }
    trips = [_resolve_trip(instance, edge_lookup, spec) for spec in TRIP_SPECS]
    _validate_candidate_edge(edge_lookup)

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "axes.titlesize": 10.3,
            "axes.titleweight": "semibold",
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.4,
            "ytick.labelsize": 7.4,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    fig = plt.figure(figsize=(12.6, 10.3), facecolor="white")
    grid = fig.add_gridspec(
        2,
        4,
        width_ratios=(1.0, 0.038, 1.0, 0.038),
        left=0.065,
        right=0.965,
        top=0.955,
        bottom=0.145,
        wspace=0.16,
        hspace=0.21,
    )
    terrain_ax = fig.add_subplot(grid[0, 0])
    terrain_blank = fig.add_subplot(grid[0, 1])
    illumination_ax = fig.add_subplot(grid[0, 2])
    illumination_cax = fig.add_subplot(grid[0, 3])
    risk_ax = fig.add_subplot(grid[1, 0])
    risk_cax = fig.add_subplot(grid[1, 1])
    route_ax = fig.add_subplot(grid[1, 2])
    route_blank = fig.add_subplot(grid[1, 3])
    terrain_blank.axis("off")
    route_blank.axis("off")

    map_extent = (0.0, extent_km, 0.0, extent_km)
    terrain_ax.imshow(
        terrain_rgba,
        extent=map_extent,
        origin="lower",
        interpolation="lanczos",
        resample=True,
    )
    terrain_ax.set_title("(a) Terrain", loc="left", pad=6.0)

    illumination_cmap = _resolve_colormap("reference_panel_a_visibility")
    illumination_norm = _build_norm(illumination, limits=(0.0, 1.0), gamma=1.08)
    illumination_image = illumination_ax.imshow(
        illumination,
        extent=map_extent,
        origin="lower",
        cmap=illumination_cmap,
        norm=illumination_norm,
        interpolation="bilinear",
        resample=True,
    )
    illumination_ax.set_title("(b) Illumination", loc="left", pad=6.0)
    illumination_ax.text(
        0.035,
        0.955,
        "Low solar visibility and PSRs\nremain traversable terrain",
        transform=illumination_ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.0,
        color="#17374E",
        bbox={
            "boxstyle": "square,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#6B8897",
            "linewidth": 0.6,
            "alpha": 0.88,
        },
        zorder=5,
    )
    illumination_colorbar = fig.colorbar(illumination_image, cax=illumination_cax)
    illumination_colorbar.set_label("average solar visibility index", fontsize=7.6)
    illumination_colorbar.ax.tick_params(labelsize=6.8, width=0.6, length=2.5)

    risk_cmap = _resolve_colormap("reference_guidance_risk")
    risk_norm = _build_norm(traversal_risk, limits=(0.1, 0.9), gamma=1.0)
    risk_image = risk_ax.imshow(
        traversal_risk,
        extent=map_extent,
        origin="lower",
        cmap=risk_cmap,
        norm=risk_norm,
        interpolation="bilinear",
        resample=True,
    )
    risk_ax.set_title("(c) Traversal risk", loc="left", pad=6.0)
    risk_colorbar = fig.colorbar(risk_image, cax=risk_cax)
    risk_colorbar.set_label("risk index", fontsize=7.6)
    risk_colorbar.ax.tick_params(labelsize=6.8, width=0.6, length=2.5)

    # The planning panel is intentionally not a composite environment map.
    route_ax.imshow(
        terrain_rgba,
        extent=map_extent,
        origin="lower",
        interpolation="lanczos",
        resample=True,
        zorder=0,
    )
    _draw_candidate_alternatives(route_ax, edge_lookup)
    for trip in trips:
        _draw_trip(route_ax, trip)
    selected_task_ids = {
        task_id
        for trip in trips
        for task_id in trip["task_ids"]
    }
    _draw_task_sites(route_ax, instance, selected_task_ids)
    _draw_depot_and_fleet(route_ax, instance)
    route_ax.set_title("(d) Fleet routes and task execution", loc="left", pad=6.0)
    route_ax.text(
        0.035,
        0.955,
        "Terrain, illumination, and risk\njointly inform path evaluation",
        transform=route_ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.0,
        color="#28343B",
        bbox={
            "boxstyle": "square,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#7B858B",
            "linewidth": 0.6,
            "alpha": 0.88,
        },
        zorder=12,
    )
    route_ax.annotate(
        "candidate paths",
        xy=(34.6, 32.8),
        xytext=(37.5, 39.5),
        fontsize=6.8,
        color="#303A40",
        ha="center",
        va="center",
        bbox={
            "boxstyle": "square,pad=0.20",
            "facecolor": "white",
            "edgecolor": "#90999F",
            "linewidth": 0.55,
            "alpha": 0.86,
        },
        arrowprops={
            "arrowstyle": "-",
            "color": "#90999F",
            "linewidth": 0.7,
        },
        zorder=12,
    )

    axes = (terrain_ax, illumination_ax, risk_ax, route_ax)
    ticks = np.linspace(0.0, extent_km, 6)
    for ax in axes:
        ax.set_xlim(0.0, extent_km)
        ax.set_ylim(0.0, extent_km)
        ax.set_aspect("equal")
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.75)
            spine.set_color("#333B40")
    terrain_ax.set_ylabel("south-north distance (km)")
    risk_ax.set_ylabel("south-north distance (km)")
    risk_ax.set_xlabel("east-west distance (km)")
    route_ax.set_xlabel("east-west distance (km)")
    terrain_ax.tick_params(labelbottom=False)
    illumination_ax.tick_params(labelbottom=False, labelleft=False)
    route_ax.tick_params(labelleft=False)

    _draw_figure_legends(fig)

    instance_id = str(instance.get("instance_id", INSTANCE_PATH.stem))
    layer_sources = {
        key: Path(value["source"]).name
        for key, value in (context.get("layer_status") or {}).items()
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
            "Title": "Separated lunar environment layers and fleet routes",
            "Description": (
                f"Instance={instance_id}; four independent panels: LOLA terrain, "
                "average solar visibility, deterministic traversal risk, and fleet routes; "
                "environment layers are not composited; three vehicles; V1 has two closed "
                "depot-to-depot trips; V2 and V3 have one each; solid legs are outbound or "
                "service legs and dashed colored legs return to the depot; three candidate "
                f"paths are actual path options for {CANDIDATE_EDGE[0]}->{CANDIDATE_EDGE[1]}; "
                "reference routes are feasible but reference_exact_status=NOT_SOLVED; "
                f"sources={layer_sources}"
            ),
            "Software": "lunar-ice-bpc deterministic Matplotlib renderer",
        },
    )
    plt.close(fig)

    print(f"wrote {OUTPUT_PATH}")
    print(f"instance_id={instance_id}")
    for trip in trips:
        print(
            f"{trip['vehicle']} trip_{trip['trip']} "
            f"tasks={','.join(trip['task_ids'])} "
            f"closed={trip['closed']} feasible={trip['feasible']}"
        )
    print("candidate_edge=depot->ice_site_009 options=low_time,low_energy,low_risk")
    print("environment_layers=separate; route_panel_background=LOLA_terrain_only")
    print("reference_exact_status=NOT_SOLVED; figure does not claim optimality")
    return 0


def _draw_figure_legends(fig: plt.Figure) -> None:
    task_handles = [
        Line2D(
            [0],
            [0],
            marker=TASK_MARKERS[mode],
            linestyle="none",
            markerfacecolor="#FFE16A",
            markeredgecolor="#11181D",
            markeredgewidth=0.8,
            markersize=6.8,
            label=label,
        )
        for mode, label in (
            ("detect", "detection"),
            ("sample", "sampling"),
            ("drill", "drilling"),
        )
    ]
    task_handles.append(
        Line2D(
            [0],
            [0],
            marker="*",
            linestyle="none",
            markerfacecolor="white",
            markeredgecolor="#11181D",
            markeredgewidth=0.9,
            markersize=10.0,
            label="depot / recharge",
        )
    )
    fleet_handles = [
        Line2D(
            [0],
            [0],
            color=color,
            linewidth=2.0,
            label=("V1: two trips" if vehicle == "V1" else f"{vehicle}: one trip"),
        )
        for vehicle, color in VEHICLE_COLORS.items()
    ]
    semantics_handles = [
        Line2D(
            [0],
            [0],
            color="#4E5961",
            linewidth=1.8,
            label="outbound / service leg",
        ),
        Line2D(
            [0],
            [0],
            color="#4E5961",
            linewidth=1.8,
            linestyle=(0, (5.0, 2.4)),
            label="return to depot",
        ),
        Line2D(
            [0],
            [0],
            color="#858F96",
            linewidth=1.8,
            linestyle=(0, (1.0, 2.0)),
            label="alternative candidate path",
        ),
    ]
    legend = fig.legend(
        handles=task_handles + fleet_handles + semantics_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.018),
        ncol=5,
        frameon=True,
        fancybox=False,
        framealpha=0.96,
        edgecolor="#CDD2D5",
        fontsize=7.2,
        handlelength=2.8,
        columnspacing=1.4,
        borderpad=0.65,
        labelspacing=0.75,
    )
    legend.get_frame().set_linewidth(0.65)


if __name__ == "__main__":
    raise SystemExit(main())

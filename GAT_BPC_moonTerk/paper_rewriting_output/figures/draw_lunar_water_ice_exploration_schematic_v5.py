#!/usr/bin/env python3
"""Render a pseudo-3D exploded stack of lunar planning layers.

The v5 composition contains five registered views of the same 50 km by 50 km
mission region.  The DEM, traversal-risk, and illumination planes show complete
candidate graphs over the displayed task set.  The upper layer uses the same
task coordinates and candidate-path geometry to communicate route selection;
it remains an illustration rather than a computed solution.
"""

from __future__ import annotations

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
import matplotlib.patheffects as path_effects
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np

from draw_lunar_instance_environment_panels import (
    _apply_detail_texture,
    _apply_relief_shading,
    _build_detail_texture,
    _build_hillshade,
    _build_norm,
    _gaussian_smooth,
    _read_raw_display_layers,
    _resolve_colormap,
    _robust_unit_index,
)
from draw_lunar_real_environment_task_sites import (
    _build_official_lola_hillshade_rgb,
    _point_at_fraction,
)
from draw_lunar_water_ice_exploration_schematic_v3 import (
    CANDIDATE_EDGE,
    TASK_MARKERS,
    VEHICLE_COLORS,
    _resolve_trip,
    _validate_candidate_edge,
)
from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


INSTANCE_PATH = ROOT / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
RAW_MAP_DIR = ROOT / "data/raw_maps"
REFERENCE_PANEL_PATH = (
    ROOT
    / "output/data_figures/lunar_sp50_020_instance_001_environment_panels_no_sites.png"
)
OUTPUT_PATH = FIGURE_DIR / "lunar_water_ice_exploration_schematic_v5.png"
OUTPUT_PDF_PATH = FIGURE_DIR / "lunar_water_ice_exploration_schematic_v5.pdf"
OUTPUT_DPI = 500

LAYER_Z = {
    "terrain": 0.0,
    "risk": 12.0,
    "illumination": 24.0,
    "routes": 36.0,
}

# Seven representative tasks are retained instead of plotting all 20 sites.
# V1 performs two closed trips; V2 performs one closed trip.
ROUTE_TRIP_SPECS = (
    {"vehicle": "V1", "journey": 0, "sortie": 0, "trip": 1},
    {"vehicle": "V1", "journey": 0, "sortie": 1, "trip": 2},
    {"vehicle": "V2", "journey": 1, "sortie": 2, "trip": 1},
)

# v5-specific composition.  The original constants and drawing helpers above
# remain available because v6 and the per-layer exporter import them.
V5_LAYER_Z = {
    "base": 0.0,
    "terrain": 10.5,
    "risk": 21.0,
    "illumination": 31.5,
    "routes": 42.0,
}
V5_CANDIDATE_PATH_TYPES = ("low_time", "low_energy", "low_risk")
V5_CANDIDATE_COLORS = {
    "low_time": "#3E78B2",
    "low_energy": "#D79A24",
    "low_risk": "#B04A7A",
}


def _build_cartoon_lunar_rover_marker() -> mpl.path.Path:
    """Return a compact rover silhouette suitable for a small route marker."""
    vertices: list[tuple[float, float]] = []
    codes: list[int] = []

    def add_polygon(points: list[tuple[float, float]]) -> None:
        vertices.extend(points)
        vertices.append(points[0])
        codes.extend(
            [mpl.path.Path.MOVETO]
            + [mpl.path.Path.LINETO] * (len(points) - 1)
            + [mpl.path.Path.CLOSEPOLY]
        )

    def add_disc(center_x: float, center_y: float, radius: float) -> None:
        angles = np.linspace(0.0, 2.0 * np.pi, 13)[:-1]
        add_polygon(
            [
                (
                    center_x + radius * float(np.cos(angle)),
                    center_y + radius * float(np.sin(angle)),
                )
                for angle in angles
            ]
        )

    # Low chassis, raised front cabin, sensor mast, and two wheels form an
    # intentionally abstract icon that remains recognizable at journal scale.
    add_polygon(
        [
            (-1.20, -0.10),
            (-1.10, 0.42),
            (0.24, 0.42),
            (0.46, 0.78),
            (0.96, 0.78),
            (1.22, 0.10),
            (1.10, -0.10),
        ]
    )
    add_polygon([(-0.67, 0.40), (-0.57, 0.40), (-0.57, 0.93), (-0.67, 0.93)])
    add_disc(-0.62, 1.01, 0.14)
    add_disc(-0.72, -0.29, 0.27)
    add_disc(0.72, -0.29, 0.27)
    return mpl.path.Path(np.asarray(vertices, dtype="float64"), codes)


V5_LUNAR_ROVER_MARKER = _build_cartoon_lunar_rover_marker()

# Seven task symbols, three vehicles, and four closed trips keep the upper layer
# legible.  These sequences use existing directed logical connections, but are
# illustrative task-allocation links rather than a solver solution.
V5_LOGICAL_TRIPS = (
    {
        "vehicle": "V1",
        "trip": 1,
        "task_ids": ("ice_site_006", "ice_site_004"),
        "bend": 1.8,
        "selected_path_types": ("low_risk", "low_energy"),
        "return_path_type": "low_time",
    },
    {
        "vehicle": "V1",
        "trip": 2,
        "task_ids": ("ice_site_009",),
        "bend": 1.8,
        "selected_path_types": ("low_time",),
        "return_path_type": "low_risk",
    },
    {
        "vehicle": "V2",
        "trip": 1,
        "task_ids": ("ice_site_001", "ice_site_003"),
        "bend": 1.8,
        "selected_path_types": ("low_energy", "low_time"),
        "return_path_type": "low_risk",
    },
    {
        "vehicle": "V3",
        "trip": 1,
        "task_ids": ("ice_site_007", "ice_site_018"),
        "bend": 1.5,
        "selected_path_types": ("low_risk", "low_energy"),
        "return_path_type": "low_time",
    },
)


def main() -> int:
    if not REFERENCE_PANEL_PATH.is_file():
        raise FileNotFoundError(
            "no-sites environment reference is unavailable: "
            f"{REFERENCE_PANEL_PATH}"
        )

    instance = read_json(INSTANCE_PATH)
    resource_map = instance["resource_map"]
    extent_km = float(resource_map["extent_km"])
    context = build_real_map_surface_context(
        raw_map_dir=RAW_MAP_DIR,
        center_x_km=float(resource_map["center_x_km"]),
        center_y_km=float(resource_map["center_y_km"]),
        extent_km=extent_km,
        output_cells=800,
        allow_remote=False,
        allow_partial=False,
    )
    if context.get("status") != "REAL_MAP_SURFACES_READY":
        raise RuntimeError(f"real lunar layers unavailable: {context.get('status')}")

    layer_rgba, layer_mappables = _build_environment_layers(
        context,
        center_x_km=float(resource_map["center_x_km"]),
        center_y_km=float(resource_map["center_y_km"]),
        extent_km=extent_km,
    )
    base_rgba = _build_official_lola_hillshade_rgb(
        official_hillshade=np.asarray(
            context["surfaces"]["hillshade"],
            dtype="float64",
        ),
    )
    edge_lookup = {
        (str(edge["from"]), str(edge["to"]), str(option["path_type"])): option
        for edge in instance["logical_graph"]["edges"]
        for option in edge.get("path_options", [])
    }
    _validate_candidate_edge(edge_lookup)
    logical_trips = [dict(spec) for spec in V5_LOGICAL_TRIPS]
    _validate_v5_logical_trips(instance, edge_lookup, logical_trips)
    displayed_legs = _collect_v5_directed_legs(instance, logical_trips)
    selected_task_ids = {
        task_id
        for trip in logical_trips
        for task_id in trip["task_ids"]
    }
    if len(selected_task_ids) != 7:
        raise ValueError(
            f"expected seven sparse representative tasks, found {len(selected_task_ids)}"
        )
    complete_candidate_legs = _collect_v5_complete_directed_graph(
        instance,
        selected_task_ids,
    )
    _validate_v5_complete_candidate_graph(
        edge_lookup,
        complete_candidate_legs,
    )

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": OUTPUT_DPI,
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(13.4, 9.0), facecolor="white")
    stack_ax = fig.add_axes(
        (0.010, 0.035, 0.745, 0.93),
        projection="3d",
        computed_zorder=False,
    )
    key_ax = fig.add_axes((0.760, 0.055, 0.225, 0.88))

    _draw_v5_environment_stack(
        stack_ax,
        base_rgba=base_rgba,
        rgba_layers=layer_rgba,
        instance=instance,
        edge_lookup=edge_lookup,
        candidate_legs=complete_candidate_legs,
        extent_km=extent_km,
    )
    _draw_v5_logical_layer(
        stack_ax,
        instance=instance,
        edge_lookup=edge_lookup,
        trips=logical_trips,
        selected_task_ids=selected_task_ids,
        extent_km=extent_km,
    )
    _format_v5_axis(stack_ax, extent_km=extent_km)
    _draw_v5_key_panel(
        key_ax,
        layer_mappables=layer_mappables,
    )

    instance_id = str(instance.get("instance_id", INSTANCE_PATH.stem))
    layer_sources = {
        key: Path(value["source"]).name
        for key, value in (context.get("layer_status") or {}).items()
        if isinstance(value, dict)
        and value.get("status") == "ready"
        and value.get("source")
    }
    figure_description = (
        f"Instance={instance_id}; bottom-to-top layers=LOLA shaded relief, DEM "
        "terrain, deterministic traversal risk, average solar visibility, and "
        "fleet route selection; all five planes use the same 50 km by 50 km "
        "spatial registration, task coordinates, and candidate-path geometry; "
        "environment appearance follows "
        "lunar_sp50_020_instance_001_environment_panels_no_sites; only the upper "
        "layer contains one depot, seven representative tasks, three vehicles, and "
        "four closed trips; the DEM, illumination, and traversal-risk layers each "
        f"show a complete directed candidate graph with {len(complete_candidate_legs)} "
        "arcs, using low-time, low-energy, and low-risk candidates respectively; "
        "candidate curvature is visually amplified to expose route heterogeneity "
        "and is not a physical trajectory reconstruction; on the logical layer, "
        "a solid link shows the selected path, including each depot return, while "
        "two dashed links show the unselected candidate paths for every directed leg; "
        "logical links are illustrative and "
        "are not physical trajectories, a feasibility or optimality proof, or solver "
        f"output; sources={layer_sources}"
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT_PATH,
        dpi=OUTPUT_DPI,
        facecolor="white",
        metadata={
            "Title": "Pseudo-3D lunar environment and fleet route-selection stack",
            "Description": figure_description,
            "Software": "lunar-ice-bpc deterministic Matplotlib 3D renderer",
        },
    )
    fig.savefig(
        OUTPUT_PDF_PATH,
        dpi=OUTPUT_DPI,
        facecolor="white",
        metadata={
            "Title": "Pseudo-3D lunar environment and fleet route-selection stack",
            "Subject": figure_description,
            "Creator": "lunar-ice-bpc deterministic Matplotlib 3D renderer",
        },
    )
    plt.close(fig)

    print(f"wrote {OUTPUT_PATH}")
    print(f"wrote {OUTPUT_PDF_PATH}")
    print(f"reference_panel={REFERENCE_PANEL_PATH}")
    print(f"instance_id={instance_id}")
    print(f"representative_task_count={len(selected_task_ids)}")
    for trip in logical_trips:
        print(
            f"{trip['vehicle']} trip_{trip['trip']} "
            f"tasks={','.join(trip['task_ids'])} closed=True"
        )
    print("layer_order=lola_shaded_relief,terrain,risk,illumination,logical_routes")
    print(f"displayed_route_leg_count={len(displayed_legs)}")
    print(f"logical_unselected_candidate_count={2 * len(displayed_legs)}")
    print(f"complete_candidate_arc_count={len(complete_candidate_legs)}")
    print("candidate_paths=complete_directed_graph; low_time@terrain,low_risk@risk,low_energy@illumination")
    print("logical_layer=one_solid_selected_path_and_two_dashed_unselected_candidate_paths_per_directed_leg")
    print("selection_semantics=illustrative; not physical trajectories or solver output")
    return 0


def _build_environment_layers(
    context: dict[str, Any],
    *,
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
) -> tuple[dict[str, np.ndarray], dict[str, mpl.cm.ScalarMappable]]:
    surfaces = context["surfaces"]
    raw_layers = _read_raw_display_layers(
        context,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=int(np.asarray(surfaces["elevation_m"]).shape[0]),
    )
    elevation = np.asarray(surfaces["elevation_m"], dtype="float64")
    values = {
        "terrain": elevation,
        "risk": np.asarray(context["risk"], dtype="float64"),
        "illumination": _robust_unit_index(
            raw_layers["lola_avg_solar_visibility"],
            lower_percentile=0.0,
            upper_percentile=99.5,
        ),
    }
    hillshade = _build_hillshade(elevation, extent_km=extent_km)
    detail_texture = _build_detail_texture(elevation, extent_km=extent_km)
    specs = {
        "terrain": {
            "cmap": "reference_lunar_terrain",
            "limits": "p01_p99",
            "gamma": 1.15,
            "sigma": 0.60,
            "relief": 0.32,
            "detail": 0.04,
        },
        "risk": {
            "cmap": "reference_guidance_risk",
            "limits": (0.1, 0.9),
            "gamma": 1.0,
            "sigma": 10.0,
            "relief": 0.23,
            "detail": 0.17,
        },
        "illumination": {
            "cmap": "reference_panel_a_visibility",
            "limits": (0.0, 1.0),
            "gamma": 1.08,
            "sigma": 10.0,
            "relief": 0.32,
            "detail": 0.20,
        },
    }
    rgba_layers: dict[str, np.ndarray] = {}
    mappables: dict[str, mpl.cm.ScalarMappable] = {}
    for key, spec in specs.items():
        display_values = _gaussian_smooth(
            values[key],
            sigma_cells=float(spec["sigma"]),
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
            strength=float(spec["relief"]),
        )
        rgba = _apply_detail_texture(
            rgba,
            detail_texture,
            valid_mask=~np.ma.getmaskarray(matrix),
            strength=float(spec["detail"]),
        )
        rgba_layers[key] = np.asarray(rgba, dtype="float64")
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        mappables[key] = mappable
    return rgba_layers, mappables


def _validate_v5_logical_trips(
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    trips: list[dict[str, Any]],
) -> None:
    """Confirm that every illustrated leg is present in the logical graph."""
    depot_id = str(instance["depot"]["id"])
    edge_pairs = {
        (str(edge["from"]), str(edge["to"]))
        for edge in instance["logical_graph"]["edges"]
    }
    for trip in trips:
        task_ids = tuple(str(task_id) for task_id in trip["task_ids"])
        unknown = [task_id for task_id in task_ids if task_id not in instance["tasks"]]
        if unknown:
            raise KeyError(f"unknown tasks in logical trip: {unknown}")
        sequence = (depot_id, *task_ids, depot_id)
        missing = [
            (source, target)
            for source, target in zip(sequence, sequence[1:])
            if (source, target) not in edge_pairs
        ]
        if missing:
            raise KeyError(f"missing directed logical connections: {missing}")
        selected_path_types = tuple(
            str(path_type) for path_type in trip["selected_path_types"]
        )
        if len(selected_path_types) != len(task_ids):
            raise ValueError(
                "each outward or inter-task leg needs one selected path type: "
                f"vehicle={trip['vehicle']} trip={trip['trip']}"
            )
        for selected_path_type in selected_path_types:
            if selected_path_type not in V5_CANDIDATE_PATH_TYPES:
                raise ValueError(f"unsupported selected path type: {selected_path_type}")
        return_path_type = str(trip["return_path_type"])
        if return_path_type not in V5_CANDIDATE_PATH_TYPES:
            raise ValueError(f"unsupported return path type: {return_path_type}")
        for source, target in zip(sequence, sequence[1:]):
            missing_options = [
                path_type
                for path_type in V5_CANDIDATE_PATH_TYPES
                if (str(source), str(target), path_type) not in edge_lookup
            ]
            if missing_options:
                raise KeyError(
                    f"missing candidates for {source}->{target}: {missing_options}"
                )


def _collect_v5_directed_legs(
    instance: dict[str, Any],
    trips: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return every directed leg in the four displayed closed trips."""
    depot_id = str(instance["depot"]["id"])
    displayed_legs: list[dict[str, Any]] = []
    for trip_index, trip in enumerate(trips):
        sequence = (depot_id, *trip["task_ids"], depot_id)
        for leg_index, (source, target) in enumerate(
            zip(sequence, sequence[1:])
        ):
            displayed_legs.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "vehicle": str(trip["vehicle"]),
                    "trip": int(trip["trip"]),
                    "trip_index": trip_index,
                    "leg_index": leg_index,
                    "is_return": leg_index == len(sequence) - 2,
                }
            )
    return displayed_legs


def _collect_v5_complete_directed_graph(
    instance: dict[str, Any],
    selected_task_ids: set[str],
) -> list[dict[str, str]]:
    """Build the complete directed graph over the depot and displayed tasks."""
    node_ids = (
        str(instance["depot"]["id"]),
        *sorted(str(task_id) for task_id in selected_task_ids),
    )
    return [
        {"source": source, "target": target}
        for source in node_ids
        for target in node_ids
        if source != target
    ]


def _validate_v5_complete_candidate_graph(
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    candidate_legs: list[dict[str, str]],
) -> None:
    node_ids = {
        node_id
        for leg in candidate_legs
        for node_id in (leg["source"], leg["target"])
    }
    expected_arc_count = len(node_ids) * (len(node_ids) - 1)
    if len(candidate_legs) != expected_arc_count:
        raise ValueError(
            f"expected {expected_arc_count} complete-graph arcs, "
            f"found {len(candidate_legs)}"
        )
    missing = [
        (leg["source"], leg["target"], path_type)
        for leg in candidate_legs
        for path_type in V5_CANDIDATE_PATH_TYPES
        if (leg["source"], leg["target"], path_type) not in edge_lookup
    ]
    if missing:
        raise KeyError(f"complete candidate graph is missing options: {missing[:8]}")


def _draw_v5_environment_stack(
    ax: plt.Axes,
    *,
    base_rgba: np.ndarray,
    rgba_layers: dict[str, np.ndarray],
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    candidate_legs: list[dict[str, str]],
    extent_km: float,
) -> None:
    """Draw five registered planes over one common spatial coordinate system."""
    _plot_image_plane(
        ax,
        base_rgba,
        z=V5_LAYER_Z["base"],
        extent_km=extent_km,
    )

    _draw_candidate_paths_on_environment_layers(
        ax,
        instance=instance,
        edge_lookup=edge_lookup,
        candidate_legs=candidate_legs,
        extent_km=extent_km,
    )
    for key in ("terrain", "risk", "illumination"):
        _plot_image_plane(
            ax,
            rgba_layers[key],
            z=V5_LAYER_Z[key],
            extent_km=extent_km,
        )

    route_rgba = np.ones((120, 120, 4), dtype="float64")
    route_rgba[..., :3] = np.asarray((0.94, 0.96, 0.97), dtype="float64")
    route_rgba[..., 3] = 0.70
    _plot_image_plane(
        ax,
        route_rgba,
        z=V5_LAYER_Z["routes"],
        extent_km=extent_km,
    )

    for x, y in (
        (0.0, 0.0),
        (extent_km, 0.0),
        (extent_km, extent_km),
        (0.0, extent_km),
    ):
        ax.plot(
            [x, x],
            [y, y],
            [V5_LAYER_Z["base"], V5_LAYER_Z["routes"]],
            color="#7C868C",
            linewidth=0.65,
            linestyle=(0, (1.5, 3.0)),
            alpha=0.55,
            zorder=0,
        )


def _draw_candidate_paths_on_environment_layers(
    ax: plt.Axes,
    *,
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    candidate_legs: list[dict[str, str]],
    extent_km: float,
) -> None:
    """Draw a complete directed candidate graph on each map plane."""
    plane_by_path_type = {
        "low_time": "terrain",
        "low_energy": "illumination",
        "low_risk": "risk",
    }
    for path_type in V5_CANDIDATE_PATH_TYPES:
        layer = plane_by_path_type[path_type]
        z = V5_LAYER_Z[layer] + 0.42
        surface_zorder = 1.0 + V5_LAYER_Z[layer] / 12.0
        color = V5_CANDIDATE_COLORS[path_type]
        node_positions: dict[str, np.ndarray] = {}
        for leg in candidate_legs:
            source = str(leg["source"])
            target = str(leg["target"])
            option = edge_lookup[(source, target, path_type)]
            raw_points = np.asarray(option["path_xy"], dtype="float64")
            points = _stylize_environment_candidate_path(
                raw_points,
                path_type=path_type,
                source=source,
                target=target,
                extent_km=extent_km,
            )
            node_positions.setdefault(source, points[0])
            node_positions.setdefault(target, points[-1])
            ax.plot(
                points[:, 0],
                points[:, 1],
                np.full(points.shape[0], z + 0.02),
                color=color,
                linewidth=0.95,
                solid_capstyle="round",
                alpha=0.52,
                zorder=surface_zorder + 0.25,
            )

        for node_id, point in node_positions.items():
            is_depot = node_id == "depot"
            marker_style = (
                "*"
                if is_depot
                else TASK_MARKERS[str(instance["tasks"][node_id]["operation_mode"])]
            )
            marker = ax.scatter(
                [float(point[0])],
                [float(point[1])],
                [z + 0.08],
                s=55 if is_depot else 40,
                marker=marker_style,
                facecolor="white" if is_depot else "#FFE16A",
                edgecolor="#11181D",
                linewidth=0.65,
                depthshade=False,
                zorder=surface_zorder + 0.30,
            )
            marker.set_zorder(surface_zorder + 0.30)


def _stylize_environment_candidate_path(
    raw_points: np.ndarray,
    *,
    path_type: str,
    source: str,
    target: str,
    extent_km: float,
) -> np.ndarray:
    """Enhance existing path curvature while preserving both endpoints."""
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
    wave = np.sin(
        2.0 * np.pi * cycles_by_type[path_type] * parameter + phase
    )
    lateral_offset = direction_sign * amplitude * envelope * (0.40 + 0.60 * wave)
    # The upper-right task carries a four-line decision bundle in the route
    # layer: three outward candidates and one selected return.  Apply the same
    # endpoint-preserving offsets in every layer so the alternatives remain
    # distinguishable without breaking cross-layer correspondence.
    if source == "depot" and target == "ice_site_009":
        bundle_offset = {
            "low_time": -1.60,
            "low_energy": 0.00,
            "low_risk": 1.60,
        }[path_type]
        lateral_offset += bundle_offset * envelope
    elif source == "ice_site_009" and target == "depot":
        bundle_offset = {
            "low_time": -3.20,
            "low_energy": -4.00,
            "low_risk": -4.80,
        }[path_type]
        lateral_offset += bundle_offset * envelope
    styled = baseline + 1.35 * (points - baseline)
    styled += lateral_offset[:, None] * normal
    styled[0] = start
    styled[-1] = end
    return np.clip(styled, 0.0, float(extent_km))


def _quadratic_curve(
    start: np.ndarray,
    end: np.ndarray,
    *,
    bend_km: float,
    point_count: int = 96,
) -> np.ndarray:
    """Return a restrained quadratic curve for a schematic logical link."""
    start = np.asarray(start, dtype="float64")
    end = np.asarray(end, dtype="float64")
    delta = end - start
    length = float(np.linalg.norm(delta))
    if length <= 1.0e-12:
        return np.repeat(start[None, :], point_count, axis=0)
    normal = np.asarray((-delta[1], delta[0]), dtype="float64") / length
    control = 0.5 * (start + end) + float(bend_km) * normal
    parameter = np.linspace(0.0, 1.0, point_count)[:, None]
    return (
        np.square(1.0 - parameter) * start
        + 2.0 * (1.0 - parameter) * parameter * control
        + np.square(parameter) * end
    )


def _draw_v5_logical_layer(
    ax: plt.Axes,
    *,
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    trips: list[dict[str, Any]],
    selected_task_ids: set[str],
    extent_km: float,
) -> None:
    """Draw route selection using the same coordinates and paths as the maps."""
    z = V5_LAYER_Z["routes"] + 1.10
    depot_id = str(instance["depot"]["id"])
    positions = {
        depot_id: np.asarray(instance["depot"]["xy_km"], dtype="float64"),
        **{
            task_id: np.asarray(instance["tasks"][task_id]["xy_km"], dtype="float64")
            for task_id in selected_task_ids
        },
    }

    for trip in trips:
        vehicle = str(trip["vehicle"])
        color = VEHICLE_COLORS[vehicle]
        sequence = (depot_id, *trip["task_ids"], depot_id)
        selected_path_types = tuple(trip["selected_path_types"])
        for index, (source, target) in enumerate(zip(sequence, sequence[1:])):
            is_return = index == len(sequence) - 2
            if is_return:
                selected_path_type = str(trip["return_path_type"])
            else:
                selected_path_type = str(selected_path_types[index])
            for path_type in V5_CANDIDATE_PATH_TYPES:
                if path_type == selected_path_type:
                    continue
                option = edge_lookup[(str(source), str(target), path_type)]
                candidate_points = _stylize_environment_candidate_path(
                    np.asarray(option["path_xy"], dtype="float64"),
                    path_type=path_type,
                    source=str(source),
                    target=str(target),
                    extent_km=extent_km,
                )
                ax.plot(
                    candidate_points[:, 0],
                    candidate_points[:, 1],
                    np.full(candidate_points.shape[0], z - 0.02),
                    color=V5_CANDIDATE_COLORS[path_type],
                    linewidth=1.15,
                    linestyle=(0, (3.0, 2.6)),
                    dash_capstyle="round",
                    alpha=0.66,
                    zorder=29,
                )

            selected_option = edge_lookup[
                (str(source), str(target), selected_path_type)
            ]
            selected_points = _stylize_environment_candidate_path(
                np.asarray(selected_option["path_xy"], dtype="float64"),
                path_type=selected_path_type,
                source=str(source),
                target=str(target),
                extent_km=extent_km,
            )
            _draw_selected_logical_curve(
                ax,
                points=selected_points,
                z=z,
                color=color,
            )

    for mode, marker in TASK_MARKERS.items():
        task_ids = [
            task_id
            for task_id in selected_task_ids
            if str(instance["tasks"][task_id]["operation_mode"]) == mode
        ]
        if not task_ids:
            continue
        task_scatter = ax.scatter(
            [float(positions[task_id][0]) for task_id in task_ids],
            [float(positions[task_id][1]) for task_id in task_ids],
            [z + 0.42] * len(task_ids),
            s=92,
            marker=marker,
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.95,
            depthshade=False,
            zorder=33,
        )
        task_scatter.set_zorder(33)

    depot_x, depot_y = (float(value) for value in positions[depot_id])
    depot_scatter = ax.scatter(
        [depot_x],
        [depot_y],
        [z + 0.50],
        s=382,
        marker="*",
        facecolor="white",
        edgecolor="#11181D",
        linewidth=1.20,
        depthshade=False,
        zorder=34,
    )
    depot_scatter.set_zorder(34)

    vehicle_positions = {
        "V1": (33.0, 39.0),
        "V2": (39.5, 14.5),
        "V3": (10.5, 21.0),
    }
    for vehicle, (vehicle_x, vehicle_y) in vehicle_positions.items():
        color = VEHICLE_COLORS[vehicle]
        vehicle_scatter = ax.scatter(
            [vehicle_x],
            [vehicle_y],
            [z + 0.56],
            s=608,
            marker=V5_LUNAR_ROVER_MARKER,
            facecolor=color,
            edgecolor="#172126",
            linewidth=1.35,
            depthshade=False,
            zorder=35,
        )
        vehicle_scatter.set_zorder(35)
        ax.text(
            vehicle_x,
            vehicle_y,
            z + 2.20,
            vehicle,
            color=color,
            fontsize=17.6,
            fontweight="bold",
            ha="center",
            va="bottom",
            zorder=36,
        )


def _draw_selected_logical_curve(
    ax: plt.Axes,
    *,
    points: np.ndarray,
    z: float,
    color: str,
) -> None:
    """Draw a selected candidate or return leg as a solid directed curve."""
    ax.plot(
        points[:, 0],
        points[:, 1],
        np.full(points.shape[0], z + 0.03),
        color=color,
        linewidth=2.75,
        linestyle="-",
        solid_capstyle="round",
        alpha=1.0,
        zorder=31,
    )
    arrow_start = _point_at_fraction(points, 0.56)
    arrow_end = _point_at_fraction(points, 0.66)
    direction = np.asarray(arrow_end) - np.asarray(arrow_start)
    length = float(np.linalg.norm(direction))
    if length <= 1.0e-9:
        return
    vector = 2.0 * direction / length
    arrow = ax.quiver(
        float(arrow_start[0]),
        float(arrow_start[1]),
        z + 0.10,
        float(vector[0]),
        float(vector[1]),
        0.0,
        color=color,
        linewidth=1.05,
        arrow_length_ratio=0.52,
        pivot="tail",
        normalize=False,
    )
    arrow.set_zorder(32)


def _format_v5_axis(ax: plt.Axes, *, extent_km: float) -> None:
    ax.set_xlim(-3.0, extent_km + 3.0)
    ax.set_ylim(-3.0, extent_km + 3.0)
    ax.set_zlim(-1.0, V5_LAYER_Z["routes"] + 7.5)
    ax.set_box_aspect((1.0, 1.0, 1.04))
    ax.view_init(elev=24.5, azim=-57.0)
    ax.set_proj_type("persp", focal_length=0.94)
    ax.set_axis_off()
    layer_labels = (
        (0.682, "(a) Logical routing\ndiagram"),
        (0.571, "(b) Average solar\nvisibility map"),
        (0.460, "(c) Traversal-risk\nmap"),
        (0.350, "(d) Digital elevation\nmodel"),
        (0.242, "(e) LOLA-derived\nshaded-relief map"),
    )
    figure = ax.get_figure()
    for y, label in layer_labels:
        figure.text(
            0.145,
            y,
            label,
            ha="right",
            va="center",
            multialignment="right",
            linespacing=1.05,
            fontsize=12.8,
            color="#28343B",
        )


def _draw_v5_key_panel(
    ax: plt.Axes,
    *,
    layer_mappables: dict[str, mpl.cm.ScalarMappable],
) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    _draw_gradient_key(
        ax,
        mappable=layer_mappables["illumination"],
        y=0.900,
        label="solar visibility index",
        low="0",
        high="1",
        label_fontsize=12.8,
        tick_fontsize=12.6,
    )
    _draw_gradient_key(
        ax,
        mappable=layer_mappables["risk"],
        y=0.800,
        label="risk index",
        low="0.1",
        high="0.9",
        label_fontsize=12.8,
        tick_fontsize=12.6,
    )
    terrain_norm = layer_mappables["terrain"].norm
    terrain_low_km = float(terrain_norm.vmin) / 1000.0
    terrain_high_km = float(terrain_norm.vmax) / 1000.0
    _draw_gradient_key(
        ax,
        mappable=layer_mappables["terrain"],
        y=0.700,
        label="elevation (km)",
        low=f"{terrain_low_km:.2f}".replace("-", "−"),
        high=f"{terrain_high_km:.2f}",
        label_fontsize=12.8,
        tick_fontsize=12.6,
    )

    ax.plot([0.03, 0.97], [0.635, 0.635], color="#D0D5D8", linewidth=0.75)
    ax.text(0.03, 0.600, "Legend", fontsize=13.4, fontweight="semibold", color="#172027")
    candidate_rows = (
        (0.545, "low_time", "low time · DEM"),
        (0.490, "low_energy", "low energy · illumination"),
        (0.435, "low_risk", "low risk · traversal risk"),
    )
    for y, path_type, label in candidate_rows:
        ax.plot(
            [0.06, 0.22],
            [y, y],
            color=V5_CANDIDATE_COLORS[path_type],
            linewidth=2.35,
            solid_capstyle="round",
        )
        ax.text(0.27, y, label, fontsize=12.6, color="#28343B", va="center")

    task_items = (
        (0.08, 0.350, "detect", "detection"),
        (0.55, 0.350, "sample", "sampling"),
        (0.08, 0.290, "drill", "drilling"),
    )
    for x, y, mode, label in task_items:
        ax.scatter(
            [x],
            [y],
            s=115,
            marker=TASK_MARKERS[mode],
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.95,
        )
        ax.text(x + 0.10, y, label, fontsize=12.6, color="#28343B", va="center")
    ax.scatter([0.55], [0.290], s=190, marker="*", facecolor="white", edgecolor="#11181D", linewidth=1.0)
    ax.text(0.65, 0.290, "depot", fontsize=12.6, color="#28343B", va="center")

    for x, vehicle in ((0.06, "V1"), (0.37, "V2"), (0.68, "V3")):
        ax.plot(
            [x, x + 0.11],
            [0.210, 0.210],
            color=VEHICLE_COLORS[vehicle],
            linewidth=2.35,
            solid_capstyle="round",
        )
        ax.text(x + 0.15, 0.210, vehicle, fontsize=12.6, color="#28343B", va="center")
    ax.plot([0.06, 0.22], [0.130, 0.130], color="#4E5961", linewidth=2.05)
    ax.text(0.27, 0.130, "selected path", fontsize=12.6, color="#28343B", va="center")
    ax.plot([0.06, 0.22], [0.065, 0.065], color="#7B858B", linewidth=1.85, linestyle=(0, (3.0, 2.6)))
    ax.text(
        0.27,
        0.065,
        "unselected\ncandidate paths",
        fontsize=12.6,
        color="#28343B",
        va="center",
        linespacing=0.95,
    )


def _draw_environment_stack(
    ax: plt.Axes,
    rgba_layers: dict[str, np.ndarray],
    *,
    extent_km: float,
) -> None:
    for key in ("terrain", "risk", "illumination"):
        _plot_image_plane(
            ax,
            rgba_layers[key],
            z=LAYER_Z[key],
            extent_km=extent_km,
        )

    # A lightly tinted glass-like plane defines the logical layer without
    # washing out its route lines and sparse task symbols.
    route_rgba = np.ones((120, 120, 4), dtype="float64")
    route_rgba[..., :3] = np.asarray((0.90, 0.93, 0.94), dtype="float64")
    route_rgba[..., 3] = 0.55
    _plot_image_plane(
        ax,
        route_rgba,
        z=LAYER_Z["routes"],
        extent_km=extent_km,
    )

    # Vertical registration guides show that every layer covers the same ROI.
    for x, y in ((0.0, 0.0), (extent_km, 0.0), (extent_km, extent_km), (0.0, extent_km)):
        ax.plot(
            [x, x],
            [y, y],
            [LAYER_Z["terrain"], LAYER_Z["routes"]],
            color="#7C868C",
            linewidth=0.65,
            linestyle=(0, (1.5, 3.0)),
            alpha=0.55,
            zorder=0,
        )


def _plot_image_plane(
    ax: plt.Axes,
    rgba: np.ndarray,
    *,
    z: float,
    extent_km: float,
) -> None:
    # Downsampling changes presentation resolution only; source values remain fixed.
    step = max(1, int(np.ceil(rgba.shape[0] / 220.0)))
    display_rgba = np.asarray(rgba[::step, ::step, :], dtype="float64")
    y = np.linspace(0.0, extent_km, display_rgba.shape[0])
    x = np.linspace(0.0, extent_km, display_rgba.shape[1])
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
        rasterized=True,
        zorder=surface_zorder,
    )
    edge_color = "#313A40"
    for x_values, y_values in (
        ((0.0, extent_km), (0.0, 0.0)),
        ((extent_km, extent_km), (0.0, extent_km)),
        ((extent_km, 0.0), (extent_km, extent_km)),
        ((0.0, 0.0), (extent_km, 0.0)),
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


def _draw_route_layer(
    ax: plt.Axes,
    *,
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    trips: list[dict[str, Any]],
    selected_task_ids: set[str],
) -> None:
    z = LAYER_Z["routes"] + 1.25

    # Two nonselected alternatives for the same depot-to-task connection.
    candidate_styles = {
        "low_time": ("#AEB7BC", (0, (3.0, 2.0))),
        "low_energy": ("#6F7A80", (0, (1.0, 2.0))),
    }
    for path_type, (color, linestyle) in candidate_styles.items():
        option = edge_lookup[(*CANDIDATE_EDGE, path_type)]
        points = np.asarray(option["path_xy"], dtype="float64")
        ax.plot(
            points[:, 0],
            points[:, 1],
            np.full(points.shape[0], z - 0.05),
            color=color,
            linewidth=1.65,
            linestyle=linestyle,
            solid_capstyle="round",
            alpha=0.92,
            zorder=20,
        )

    for trip in trips:
        color = VEHICLE_COLORS[trip["vehicle"]]
        for index, leg_item in enumerate(trip["legs"]):
            points = np.asarray(leg_item["points"], dtype="float64")
            is_return = index == len(trip["legs"]) - 1
            linestyle = (0, (5.0, 2.5)) if is_return else "-"
            # Pale under-stroke keeps the route readable against the top plane.
            ax.plot(
                points[:, 0],
                points[:, 1],
                np.full(points.shape[0], z),
                color="#243138",
                linewidth=4.2,
                linestyle=linestyle,
                solid_capstyle="round",
                dash_capstyle="round",
                alpha=0.48,
                zorder=21,
            )
            ax.plot(
                points[:, 0],
                points[:, 1],
                np.full(points.shape[0], z + 0.03),
                color=color,
                linewidth=2.65,
                linestyle=linestyle,
                solid_capstyle="round",
                dash_capstyle="round",
                alpha=1.0,
                zorder=22,
            )
            start = _point_at_fraction(points, 0.55)
            end = _point_at_fraction(points, 0.66)
            delta = np.asarray(end) - np.asarray(start)
            length = float(np.linalg.norm(delta))
            if length > 1.0e-9:
                direction = 2.2 * delta / length
                arrow = ax.quiver(
                    float(start[0]),
                    float(start[1]),
                    z + 0.12,
                    float(direction[0]),
                    float(direction[1]),
                    0.0,
                    color=color,
                    linewidth=1.15,
                    arrow_length_ratio=0.50,
                    pivot="tail",
                    normalize=False,
                )
                arrow.set_zorder(23)

    for mode, marker in TASK_MARKERS.items():
        tasks = [
            instance["tasks"][task_id]
            for task_id in selected_task_ids
            if str(instance["tasks"][task_id]["operation_mode"]) == mode
        ]
        if not tasks:
            continue
        task_scatter = ax.scatter(
            [float(task["xy_km"][0]) for task in tasks],
            [float(task["xy_km"][1]) for task in tasks],
            [z + 0.42] * len(tasks),
            s=78,
            marker=marker,
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.9,
            depthshade=False,
            zorder=24,
        )
        task_scatter.set_zorder(24)

    depot_x, depot_y = (float(value) for value in instance["depot"]["xy_km"])
    depot_scatter = ax.scatter(
        [depot_x],
        [depot_y],
        [z + 0.48],
        s=255,
        marker="*",
        facecolor="white",
        edgecolor="#11181D",
        linewidth=1.15,
        depthshade=False,
        zorder=25,
    )
    depot_scatter.set_zorder(25)
    for vehicle, dx, dy in (("V1", -2.6, 1.2), ("V2", 2.2, 1.4)):
        color = VEHICLE_COLORS[vehicle]
        vehicle_scatter = ax.scatter(
            [depot_x + dx],
            [depot_y + dy],
            [z + 0.54],
            s=42,
            marker="D",
            facecolor=color,
            edgecolor="white",
            linewidth=0.8,
            depthshade=False,
            zorder=26,
        )
        vehicle_scatter.set_zorder(26)
        ax.text(
            depot_x + dx,
            depot_y + dy,
            z + 1.10,
            vehicle,
            color=color,
            fontsize=7.0,
            fontweight="semibold",
            ha="center",
            va="bottom",
            zorder=27,
        )


def _format_stack_axis(ax: plt.Axes, *, extent_km: float) -> None:
    ax.set_xlim(-3.0, extent_km + 3.0)
    ax.set_ylim(-3.0, extent_km + 3.0)
    ax.set_zlim(-1.0, LAYER_Z["routes"] + 7.5)
    ax.set_box_aspect((1.0, 1.0, 0.93))
    ax.view_init(elev=25.5, azim=-57.0)
    ax.set_proj_type("persp", focal_length=0.92)
    ax.set_axis_off()
    ax.text2D(
        0.035,
        0.965,
        "Registered lunar environment and routing layers",
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
        "All planes represent the same 50 km × 50 km mission region",
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

    ax.text(0.03, 0.965, "Layer order", fontsize=9.5, fontweight="semibold", color="#172027")
    layer_rows = (
        (0.875, "4", "Logical routes", "#EDF2F4"),
        (0.800, "3", "Illumination", "#6F929D"),
        (0.725, "2", "Traversal risk", "#C15C70"),
        (0.650, "1", "Terrain", "#7FAE92"),
    )
    for y, number, label, color in layer_rows:
        ax.add_patch(
            Rectangle(
                (0.07, y),
                0.27,
                0.050,
                facecolor=color,
                edgecolor="#364047",
                linewidth=0.65,
            )
        )
        ax.text(0.205, y + 0.025, number, ha="center", va="center", fontsize=7.0, fontweight="bold", color="#172027")
        ax.text(0.40, y + 0.025, label, ha="left", va="center", fontsize=7.7, color="#28343B")
    ax.add_patch(
        FancyArrowPatch(
            (0.035, 0.655),
            (0.035, 0.928),
            arrowstyle="-|>",
            mutation_scale=9.0,
            linewidth=0.8,
            color="#667178",
        )
    )

    _draw_gradient_key(
        ax,
        mappable=layer_mappables["illumination"],
        y=0.565,
        label="solar visibility index",
        low="0",
        high="1",
    )
    _draw_gradient_key(
        ax,
        mappable=layer_mappables["risk"],
        y=0.482,
        label="risk index",
        low="0.1",
        high="0.9",
    )

    ax.plot([0.03, 0.97], [0.420, 0.420], color="#D0D5D8", linewidth=0.7)
    ax.text(0.03, 0.392, "Sparse routing layer", fontsize=9.0, fontweight="semibold", color="#172027")
    ax.text(0.03, 0.358, f"{selected_task_count} representative tasks; 2 vehicles; 3 closed trips", fontsize=6.8, color="#5A656C")

    task_rows = (
        ("detect", "detection"),
        ("sample", "sampling"),
        ("drill", "drilling"),
    )
    for index, (mode, label) in enumerate(task_rows):
        y = 0.317 - 0.046 * index
        ax.scatter(
            [0.10],
            [y],
            s=48,
            marker=TASK_MARKERS[mode],
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.8,
        )
        ax.text(0.19, y, label, fontsize=7.2, color="#28343B", va="center")
    ax.scatter([0.10], [0.179], s=92, marker="*", facecolor="white", edgecolor="#11181D", linewidth=0.9)
    ax.text(0.19, 0.179, "depot / recharge", fontsize=7.2, color="#28343B", va="center")

    route_rows = (
        ("V1", "two trips"),
        ("V2", "one trip"),
    )
    for index, (vehicle, label) in enumerate(route_rows):
        y = 0.132 - 0.041 * index
        ax.plot([0.06, 0.21], [y, y], color=VEHICLE_COLORS[vehicle], linewidth=2.1, solid_capstyle="round")
        ax.text(0.25, y, f"{vehicle}: {label}", fontsize=7.0, color="#28343B", va="center")
    ax.plot([0.53, 0.68], [0.132, 0.132], color="#4E5961", linewidth=1.7)
    ax.text(0.72, 0.132, "service", fontsize=6.7, color="#28343B", va="center")
    ax.plot([0.53, 0.68], [0.091, 0.091], color="#4E5961", linewidth=1.7, linestyle=(0, (5.0, 2.5)))
    ax.text(0.72, 0.091, "return", fontsize=6.7, color="#28343B", va="center")
    ax.plot([0.53, 0.68], [0.052, 0.052], color="#6F7A80", linewidth=1.5, linestyle=(0, (1.0, 2.0)))
    ax.text(0.72, 0.052, "alternative", fontsize=6.7, color="#28343B", va="center")

    ax.text(
        0.03,
        0.010,
        "Reference trips are feasible; no optimality claim is made.",
        fontsize=6.4,
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
    label_fontsize: float = 6.7,
    tick_fontsize: float = 6.1,
) -> None:
    if mappable.norm.vmin is not None and mappable.norm.vmax is not None:
        values = np.linspace(
            float(mappable.norm.vmin),
            float(mappable.norm.vmax),
            256,
        )[None, :]
        rgba = mappable.to_rgba(values)
    else:
        rgba = mappable.cmap(np.linspace(0.0, 1.0, 256)[None, :])
    ax.imshow(
        rgba,
        extent=(0.08, 0.90, y, y + 0.027),
        origin="lower",
        aspect="auto",
        interpolation="bilinear",
        zorder=1,
    )
    ax.add_patch(
        Rectangle(
            (0.08, y),
            0.82,
            0.027,
            facecolor="none",
            edgecolor="#4C565C",
            linewidth=0.55,
            zorder=2,
        )
    )
    ax.text(
        0.08,
        y + 0.036,
        label,
        fontsize=label_fontsize,
        color="#39444A",
        ha="left",
        va="bottom",
    )
    ax.text(
        0.08,
        y - 0.009,
        low,
        fontsize=tick_fontsize,
        color="#5A656C",
        ha="center",
        va="top",
    )
    ax.text(
        0.90,
        y - 0.009,
        high,
        fontsize=tick_fontsize,
        color="#5A656C",
        ha="center",
        va="top",
    )


if __name__ == "__main__":
    raise SystemExit(main())

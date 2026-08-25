#!/usr/bin/env python3
"""Draw a layered, data-backed lunar multi-vehicle routing scenario."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib.transforms import Affine2D
import numpy as np

from draw_lunar_instance_environment_panels import _gaussian_smooth
from draw_lunar_real_environment_task_sites import (
    _build_official_lola_hillshade_rgb,
    _point_at_fraction,
)
from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


INSTANCE_PATH = ROOT / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
RAW_MAP_DIR = ROOT / "data/raw_maps"
OUTPUT_PATH = Path(__file__).with_name("lunar_water_ice_exploration_schematic_v3.png")

VEHICLE_COLORS = {
    "V1": "#007F86",
    "V2": "#D95F02",
    "V3": "#6F4C9B",
}
TASK_MARKERS = {
    "detect": "o",
    "sample": "^",
    "drill": "s",
}

# One vehicle has two trips so that the fleet and multi-trip structure are both visible.
TRIP_SPECS = (
    {"vehicle": "V1", "journey": 0, "sortie": 0, "trip": 1},
    {"vehicle": "V1", "journey": 0, "sortie": 1, "trip": 2},
    {"vehicle": "V2", "journey": 1, "sortie": 2, "trip": 1},
    {"vehicle": "V3", "journey": 2, "sortie": 2, "trip": 1},
)

# This selected edge has exactly three actual path options in the instance.
CANDIDATE_EDGE = ("depot", "ice_site_009")


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
        _gaussian_smooth(np.asarray(surfaces["illumination"], dtype="float64"), sigma_cells=4.0)
    )
    traversal_risk = np.flipud(
        _gaussian_smooth(np.asarray(surfaces["risk"], dtype="float64"), sigma_cells=4.0)
    )
    illumination_rgba = _illumination_overlay(illumination)
    risk_rgba = _risk_overlay(traversal_risk)

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
            "axes.titlesize": 11.0,
            "axes.titleweight": "semibold",
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(12.8, 7.45), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=(4.45, 1.38), wspace=0.035)
    ax = fig.add_subplot(grid[0, 0])
    key_ax = fig.add_subplot(grid[0, 1])

    map_extent = (0.0, extent_km, 0.0, extent_km)
    ax.imshow(
        terrain_rgba,
        extent=map_extent,
        origin="lower",
        interpolation="lanczos",
        resample=True,
        zorder=0,
    )
    ax.imshow(
        illumination_rgba,
        extent=map_extent,
        origin="lower",
        interpolation="bilinear",
        resample=True,
        zorder=1,
    )
    ax.imshow(
        risk_rgba,
        extent=map_extent,
        origin="lower",
        interpolation="bilinear",
        resample=True,
        zorder=2,
    )

    # The two nonselected paths are placed directly on the map under the selected V1 path.
    _draw_candidate_alternatives(ax, edge_lookup)
    for trip in trips:
        _draw_trip(ax, trip)

    selected_task_ids = {
        task_id
        for trip in trips
        for task_id in trip["task_ids"]
    }
    _draw_task_sites(ax, instance, selected_task_ids)
    _draw_depot_and_fleet(ax, instance)

    ax.annotate(
        "candidate paths",
        xy=(34.5, 32.8),
        xytext=(27.2, 40.8),
        fontsize=7.9,
        color="#20262B",
        ha="left",
        va="center",
        bbox={
            "boxstyle": "square,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#8D969D",
            "linewidth": 0.7,
            "alpha": 0.86,
        },
        arrowprops={
            "arrowstyle": "-",
            "color": "#8D969D",
            "linewidth": 0.8,
            "shrinkA": 2.0,
            "shrinkB": 2.0,
        },
        zorder=12,
    )
    ax.annotate(
        "PSR / low solar visibility\ntraversable, not an obstacle",
        xy=(42.2, 38.3),
        xytext=(30.2, 46.0),
        fontsize=7.6,
        color="#143D59",
        ha="left",
        va="center",
        bbox={
            "boxstyle": "square,pad=0.28",
            "facecolor": "white",
            "edgecolor": "#4D86A5",
            "linewidth": 0.8,
            "alpha": 0.88,
        },
        arrowprops={
            "arrowstyle": "->",
            "color": "#4D86A5",
            "linewidth": 0.9,
            "shrinkA": 2.0,
            "shrinkB": 3.0,
        },
        zorder=12,
    )

    ax.set_title("(a) Integrated lunar environment and fleet routes", loc="left", pad=7.0)
    ax.set_xlim(0.0, extent_km)
    ax.set_ylim(0.0, extent_km)
    ax.set_aspect("equal")
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ticks = np.linspace(0.0, extent_km, 6)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.grid(False)

    _draw_key_panel(key_ax)
    instance_id = str(instance.get("instance_id", INSTANCE_PATH.stem))
    layer_sources = {
        key: Path(value["source"]).name
        for key, value in (context.get("layer_status") or {}).items()
        if isinstance(value, dict) and value.get("status") == "ready" and value.get("source")
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT_PATH,
        bbox_inches="tight",
        pad_inches=0.045,
        facecolor="white",
        metadata={
            "Title": "Layered lunar multi-vehicle water-ice exploration scenario",
            "Description": (
                f"Instance={instance_id}; terrain=official LOLA hillshade; "
                "middle layer=average solar visibility and shadow exposure; "
                "top layer=deterministic traversal risk; three vehicles; "
                "V1 has two closed depot-to-depot trips; V2 and V3 have one each; "
                "solid legs are outbound/service legs; dashed colored legs return to depot; "
                "the three candidate paths are actual path options for depot->ice_site_009; "
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
    print("reference_exact_status=NOT_SOLVED; figure does not claim optimality")
    return 0


def _illumination_overlay(illumination: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(illumination, dtype="float64"), 0.0, 1.0)
    rgba = np.zeros((*values.shape, 4), dtype="float64")
    rgba[..., :3] = np.asarray((0.10, 0.36, 0.56), dtype="float64")
    rgba[..., 3] = 0.30 * np.power(1.0 - values, 1.20)
    rgba[..., 3] = np.where(np.isfinite(values), rgba[..., 3], 0.0)
    return rgba


def _risk_overlay(risk: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(risk, dtype="float64"), 0.0, 1.0)
    cmap = LinearSegmentedColormap.from_list(
        "transparent_risk",
        ("#F2D06B", "#E88945", "#B93A32"),
        N=512,
    )
    rgba = cmap(values)
    strength = np.clip((values - 0.26) / 0.60, 0.0, 1.0)
    rgba[..., 3] = 0.34 * np.power(strength, 1.15)
    rgba[..., 3] = np.where(np.isfinite(values), rgba[..., 3], 0.0)
    return rgba


def _resolve_trip(
    instance: dict[str, Any],
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    reference = instance["reference_solution"]
    journey = reference["journeys"][int(spec["journey"])]
    sortie = journey["sorties"][int(spec["sortie"])]
    if str(journey.get("vehicle_id")) != f"rover_{int(spec['journey']) + 1:02d}":
        raise ValueError("unexpected reference vehicle assignment")
    if not bool(sortie.get("feasible")):
        raise ValueError("selected reference sortie is not feasible")
    legs: list[dict[str, Any]] = []
    for leg in sortie["legs"]:
        key = (str(leg["from"]), str(leg["to"]), str(leg["path_type"]))
        option = edge_lookup.get(key)
        if option is None:
            raise KeyError(f"missing path option for selected leg: {key}")
        points = np.asarray(option["path_xy"], dtype="float64")
        if points.ndim != 2 or points.shape[0] < 2 or points.shape[1] != 2:
            raise ValueError(f"invalid geometry for selected leg: {key}")
        legs.append({"leg": leg, "points": points})
    closed = bool(legs[0]["leg"]["from"] == "depot" and legs[-1]["leg"]["to"] == "depot")
    if not closed:
        raise ValueError("every illustrated trip must begin and end at the depot")
    return {
        "vehicle": str(spec["vehicle"]),
        "trip": int(spec["trip"]),
        "task_ids": [str(task_id) for task_id in sortie["tasks"]],
        "feasible": bool(sortie["feasible"]),
        "closed": closed,
        "legs": legs,
    }


def _validate_candidate_edge(
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    for path_type in ("low_time", "low_energy", "low_risk"):
        if (*CANDIDATE_EDGE, path_type) not in edge_lookup:
            raise KeyError(f"candidate edge lacks path option: {path_type}")


def _draw_candidate_alternatives(
    ax: plt.Axes,
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    styles = {
        "low_time": ("#E8ECEF", (0, (2.2, 2.0))),
        "low_energy": ("#9DA7AE", (0, (1.0, 2.0))),
    }
    for path_type, (color, linestyle) in styles.items():
        option = edge_lookup[(*CANDIDATE_EDGE, path_type)]
        points = np.asarray(option["path_xy"], dtype="float64")
        line = ax.plot(
            points[:, 0],
            points[:, 1],
            color=color,
            linewidth=2.0,
            linestyle=linestyle,
            solid_capstyle="round",
            dash_capstyle="round",
            zorder=3.2,
        )[0]
        line.set_path_effects(
            [
                path_effects.Stroke(linewidth=3.4, foreground="#20262B", alpha=0.56),
                path_effects.Normal(),
            ]
        )


def _draw_trip(ax: plt.Axes, trip: dict[str, Any]) -> None:
    color = VEHICLE_COLORS[trip["vehicle"]]
    for index, leg_item in enumerate(trip["legs"]):
        points = leg_item["points"]
        is_return = index == len(trip["legs"]) - 1
        linestyle = (0, (5.0, 2.4)) if is_return else "-"
        line = ax.plot(
            points[:, 0],
            points[:, 1],
            color=color,
            linewidth=2.15,
            linestyle=linestyle,
            solid_capstyle="round",
            dash_capstyle="round",
            alpha=0.98,
            zorder=5.0,
        )[0]
        line.set_path_effects(
            [
                path_effects.Stroke(linewidth=3.7, foreground="white", alpha=0.90),
                path_effects.Normal(),
            ]
        )
        start = _point_at_fraction(points, 0.56)
        end = _point_at_fraction(points, 0.63)
        arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=11.0,
            linewidth=1.45,
            facecolor=color,
            edgecolor=color,
            shrinkA=0.0,
            shrinkB=0.0,
            zorder=5.7,
        )
        arrow.set_path_effects(
            [
                path_effects.Stroke(linewidth=2.8, foreground="white", alpha=0.92),
                path_effects.Normal(),
            ]
        )
        ax.add_patch(arrow)


def _draw_task_sites(
    ax: plt.Axes,
    instance: dict[str, Any],
    selected_task_ids: set[str],
) -> None:
    for operation_mode, marker in TASK_MARKERS.items():
        tasks = [
            task
            for task in instance["tasks"].values()
            if str(task.get("operation_mode")) == operation_mode
        ]
        unselected = [task for task in tasks if str(task["id"]) not in selected_task_ids]
        selected = [task for task in tasks if str(task["id"]) in selected_task_ids]
        if unselected:
            ax.scatter(
                [float(task["xy_km"][0]) for task in unselected],
                [float(task["xy_km"][1]) for task in unselected],
                s=34,
                marker=marker,
                facecolor="#F1E2A7",
                edgecolor="#1D252B",
                linewidth=0.65,
                alpha=0.76,
                zorder=6.0,
            )
        if selected:
            ax.scatter(
                [float(task["xy_km"][0]) for task in selected],
                [float(task["xy_km"][1]) for task in selected],
                s=71,
                marker=marker,
                facecolor="#FFE16A",
                edgecolor="#11181D",
                linewidth=1.0,
                zorder=7.2,
            )


def _draw_depot_and_fleet(ax: plt.Axes, instance: dict[str, Any]) -> None:
    depot_x, depot_y = (float(value) for value in instance["depot"]["xy_km"])
    ax.scatter(
        [depot_x],
        [depot_y],
        s=285,
        marker="*",
        facecolor="white",
        edgecolor="#11181D",
        linewidth=1.15,
        zorder=8.0,
    )
    offsets = ((-2.45, 1.55), (0.0, 2.75), (2.45, 1.55))
    for (vehicle, color), (dx, dy) in zip(VEHICLE_COLORS.items(), offsets):
        _draw_rover_glyph(
            ax,
            x=depot_x + dx,
            y=depot_y + dy,
            color=color,
            label=vehicle,
        )


def _draw_rover_glyph(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    color: str,
    label: str,
) -> None:
    transform = Affine2D().rotate_deg_around(x, y, 0.0) + ax.transData
    body = Rectangle(
        (x - 0.48, y - 0.30),
        0.96,
        0.60,
        facecolor="white",
        edgecolor=color,
        linewidth=1.25,
        transform=transform,
        zorder=9.0,
    )
    ax.add_patch(body)
    for wx in (x - 0.39, x + 0.39):
        for wy in (y - 0.42, y + 0.42):
            ax.add_patch(
                Circle(
                    (wx, wy),
                    radius=0.12,
                    facecolor="#11181D",
                    edgecolor="white",
                    linewidth=0.4,
                    zorder=9.2,
                )
            )
    ax.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        fontsize=6.2,
        fontweight="semibold",
        color=color,
        zorder=9.4,
    )


def _draw_key_panel(ax: plt.Axes) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.set_title("(b) Layer and symbol key", loc="left", pad=7.0)

    ax.text(0.04, 0.925, "Composite map", fontsize=9.2, fontweight="semibold", color="#1D252B")
    layer_items = (
        (0.835, "Layer 3", "traversal risk", "#D55A3A", "////"),
        (0.765, "Layer 2", "solar visibility / shadow", "#4D86A5", "...."),
        (0.695, "Layer 1", "LOLA shaded relief", "#A5AAAE", None),
    )
    for y, number, label, color, hatch in layer_items:
        rectangle = Rectangle(
            (0.06, y),
            0.23,
            0.052,
            facecolor=color,
            edgecolor="#333A3F",
            linewidth=0.65,
            alpha=0.62,
            hatch=hatch,
            zorder=2,
        )
        ax.add_patch(rectangle)
        ax.text(0.34, y + 0.036, number, fontsize=7.4, fontweight="semibold", color="#1D252B", va="center")
        ax.text(0.34, y + 0.014, label, fontsize=7.3, color="#404A51", va="center")
    ax.annotate(
        "",
        xy=(0.175, 0.680),
        xytext=(0.175, 0.900),
        arrowprops={"arrowstyle": "->", "color": "#5F6A72", "linewidth": 0.8},
    )
    ax.text(0.06, 0.645, "All three layers are rendered in the same coordinate system.", fontsize=6.8, color="#5B666E", wrap=True)
    ax.text(0.06, 0.611, "PSR indicates exposure conditions; it is not blocked terrain.", fontsize=6.8, color="#315C75", wrap=True)

    ax.plot([0.04, 0.96], [0.575, 0.575], color="#CFD4D7", linewidth=0.7)
    ax.text(0.04, 0.540, "Task types", fontsize=9.0, fontweight="semibold", color="#1D252B")
    task_rows = (("o", "detection"), ("^", "sampling"), ("s", "drilling"))
    for index, (marker, label) in enumerate(task_rows):
        y = 0.498 - 0.052 * index
        ax.scatter([0.11], [y], s=61, marker=marker, facecolor="#FFE16A", edgecolor="#11181D", linewidth=0.85)
        ax.text(0.20, y, label, fontsize=7.8, color="#1D252B", va="center")
    ax.scatter([0.11], [0.342], s=105, marker="*", facecolor="white", edgecolor="#11181D", linewidth=0.9)
    ax.text(0.20, 0.342, "depot / recharge", fontsize=7.8, color="#1D252B", va="center")

    ax.plot([0.04, 0.96], [0.307, 0.307], color="#CFD4D7", linewidth=0.7)
    ax.text(0.04, 0.274, "Fleet and trips", fontsize=9.0, fontweight="semibold", color="#1D252B")
    fleet_rows = (("V1", "two depot-to-depot trips"), ("V2", "one depot-to-depot trip"), ("V3", "one depot-to-depot trip"))
    for index, (vehicle, label) in enumerate(fleet_rows):
        y = 0.234 - 0.046 * index
        color = VEHICLE_COLORS[vehicle]
        ax.plot([0.07, 0.21], [y, y], color=color, linewidth=2.1, solid_capstyle="round")
        ax.text(0.25, y, f"{vehicle}: {label}", fontsize=7.35, color="#1D252B", va="center")

    ax.plot([0.04, 0.96], [0.108, 0.108], color="#CFD4D7", linewidth=0.7)
    ax.plot([0.07, 0.21], [0.076, 0.076], color="#4E5961", linewidth=1.8)
    ax.text(0.25, 0.076, "outbound / service leg", fontsize=7.2, color="#1D252B", va="center")
    ax.plot([0.07, 0.21], [0.043, 0.043], color="#4E5961", linewidth=1.8, linestyle=(0, (5.0, 2.4)))
    ax.text(0.25, 0.043, "return to depot", fontsize=7.2, color="#1D252B", va="center")
    ax.text(0.04, 0.010, "Path and layer values are fixed within one mission epoch.", fontsize=6.55, color="#5B666E")


if __name__ == "__main__":
    raise SystemExit(main())

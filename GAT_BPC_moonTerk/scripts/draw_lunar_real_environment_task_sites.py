#!/usr/bin/env python3
"""Draw task sites and a depot over a realistic real-raster lunar environment."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib.transforms import Affine2D
from matplotlib.lines import Line2D
import numpy as np

from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


DEFAULT_INSTANCE = "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
DEFAULT_RAW_MAP_DIR = "data/raw_maps"
DEFAULT_OUTPUT = "output/data_figures/lunar_sp50_020_instance_001_real_environment.png"
DEFAULT_MISSION_OUTPUT = (
    "output/data_figures/"
    "lunar_sp50_020_instance_001_real_environment_mission_process.png"
)
DEFAULT_SCHEMATIC_V5_SITES_OUTPUT = (
    "output/data_figures/"
    "lunar_sp50_020_instance_001_real_environment_schematic_v5_sites.png"
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

# Presentation-only adjustment shared with the accepted four-panel figure.
DISPLAY_TASK_POSITION_OVERRIDES = {
    "ice_site_006": (45.0, 41.0),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Draw the selected 20-task instance over a realistic lunar environment."
    )
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument("--raw-map-dir", default=DEFAULT_RAW_MAP_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--output-cells", type=int, default=1000)
    parser.add_argument(
        "--show-mission-process",
        action="store_true",
        help=(
            "overlay one feasible reference sortie with schematic rover and "
            "water-ice detection stages"
        ),
    )
    parser.add_argument(
        "--schematic-v5-sites",
        action="store_true",
        help=(
            "replace the 20 generic task markers with the depot and seven "
            "typed task sites used by the top layer of schematic v5"
        ),
    )
    parser.add_argument("--reference-journey-index", type=int, default=0)
    parser.add_argument("--reference-sortie-index", type=int, default=0)
    args = parser.parse_args()
    if args.show_mission_process and args.schematic_v5_sites:
        parser.error("--show-mission-process and --schematic-v5-sites are exclusive")

    instance_path = _project_path(args.instance)
    raw_map_dir = _project_path(args.raw_map_dir)
    output_value = args.output
    if args.show_mission_process and output_value == DEFAULT_OUTPUT:
        output_value = DEFAULT_MISSION_OUTPUT
    elif args.schematic_v5_sites and output_value == DEFAULT_OUTPUT:
        output_value = DEFAULT_SCHEMATIC_V5_SITES_OUTPUT
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
            "real lunar raster construction failed: "
            f"status={context.get('status')} "
            f"missing={context.get('missing_required_lola_layers')}"
        )

    all_tasks = instance.get("tasks") or {}
    if args.schematic_v5_sites:
        missing_task_ids = [
            task_id for task_id in SCHEMATIC_V5_TASK_IDS if task_id not in all_tasks
        ]
        if missing_task_ids:
            raise KeyError(f"missing schematic-v5 task sites: {missing_task_ids}")
        tasks = [all_tasks[task_id] for task_id in SCHEMATIC_V5_TASK_IDS]
    else:
        tasks = list(all_tasks.values())
    depot = instance.get("depot") or {}
    depot_xy = depot.get("xy_km")
    if not tasks or not isinstance(depot_xy, list) or len(depot_xy) != 2:
        raise ValueError("instance must contain task sites and one depot coordinate")

    surfaces = context["surfaces"]
    official_hillshade = np.asarray(surfaces["hillshade"], dtype="float64")
    if not np.isfinite(official_hillshade).any():
        raise RuntimeError("official LOLA hillshade crop contains no finite values")
    lunar_rgb = _build_official_lola_hillshade_rgb(
        official_hillshade=official_hillshade,
    )

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 400,
            "figure.facecolor": (
                "white" if args.schematic_v5_sites else "#f8f8f6"
            ),
            "axes.facecolor": "#111318",
            "axes.titlesize": 12,
            "axes.titleweight": "semibold",
            "axes.labelsize": 18,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
        }
    )
    fig, ax = plt.subplots(
        figsize=(9.2, 8.1),
        constrained_layout=True,
        facecolor="white" if args.schematic_v5_sites else "#f8f8f6",
    )
    ax.imshow(
        lunar_rgb,
        extent=(0.0, extent_km, 0.0, extent_km),
        origin="lower",
        interpolation="lanczos",
        resample=True,
        zorder=0,
    )
    if args.schematic_v5_sites:
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
                s=252,
                c="#FFE16A",
                edgecolors="#11181D",
                linewidths=1.25,
                marker=marker,
                zorder=5,
            )
    else:
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
            s=101,
            c="#ffe05b",
            edgecolors="#111318",
            linewidths=1.05,
            marker="o",
            zorder=5,
        )
    ax.scatter(
        [float(depot_xy[0])],
        [float(depot_xy[1])],
        s=1008 if args.schematic_v5_sites else 671,
        c="white" if args.schematic_v5_sites else "#43d9c0",
        edgecolors="#11181D" if args.schematic_v5_sites else "#0c1116",
        linewidths=1.65 if args.schematic_v5_sites else 1.55,
        marker="*",
        zorder=6,
    )

    mission_summary: dict[str, Any] | None = None
    if args.show_mission_process:
        mission_summary = _draw_reference_mission_process(
            ax,
            instance,
            journey_index=int(args.reference_journey_index),
            sortie_index=int(args.reference_sortie_index),
        )

    coordinate_ticks = np.linspace(0.0, extent_km, 6)
    ax.set_xticks(coordinate_ticks)
    ax.set_yticks(coordinate_ticks)
    ax.set_xlim(0.0, extent_km)
    ax.set_ylim(0.0, extent_km)
    ax.set_aspect("equal")
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    if args.schematic_v5_sites:
        title = "LOLA south-pole shaded relief with representative mission sites"
    elif mission_summary is None:
        title = "LOLA south-pole shaded relief with mission sites"
    else:
        title = "Water-ice detection process on LOLA shaded relief"
    ax.set_title(title, loc="left")
    ax.grid(color="white", alpha=0.075, linewidth=0.42)
    if args.schematic_v5_sites:
        legend_handles = [
            Line2D(
                [0],
                [0],
                marker=marker,
                linestyle="none",
                markerfacecolor="#FFE16A",
                markeredgecolor="#11181D",
                markeredgewidth=0.9,
                markersize=10.4,
                label=label,
            )
            for operation_mode, marker, label in (
                ("detect", "o", "detection"),
                ("sample", "^", "sampling"),
                ("drill", "s", "drilling"),
            )
            if any(
                str(task.get("operation_mode", "")) == operation_mode
                for task in tasks
            )
        ]
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="*",
                linestyle="none",
                markerfacecolor="white",
                markeredgecolor="#11181D",
                markeredgewidth=1.0,
                markersize=11.4,
                label="depot",
            )
        )
    else:
        legend_handles = [
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor="#ffe05b",
                markeredgecolor="#111318",
                markeredgewidth=0.9,
                markersize=10.4,
                label=f"task sites (n={len(tasks)})",
            ),
            Line2D(
                [0],
                [0],
                marker="*",
                linestyle="none",
                markerfacecolor="#43d9c0",
                markeredgecolor="#0c1116",
                markeredgewidth=1.0,
                markersize=10.4,
                label="depot",
            ),
        ]
    ax.legend(
        handles=legend_handles,
        loc="center left" if args.schematic_v5_sites else "upper left",
        bbox_to_anchor=(0.012, 0.58) if args.schematic_v5_sites else (0.012, 0.988),
        ncol=1,
        fontsize=16,
        frameon=True,
        framealpha=0.86,
        facecolor="#f8f8f6",
        edgecolor="#d0d0cc",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    instance_id = str(instance.get("instance_id", instance_path.stem))
    fig.savefig(
        output_path,
        bbox_inches="tight",
        facecolor="white" if args.schematic_v5_sites else fig.get_facecolor(),
        transparent=False,
        metadata={
            "Title": (
                f"Official LOLA shaded relief with sites for {instance_id}"
                if mission_summary is None
                else f"Water-ice detection process for {instance_id}"
            ),
            "Description": (
                "NASA GSFC PGDA LDEM_80S_80MPP_ADJ_HILL.TIF official LOLA 80 m/pixel "
                "shaded-relief crop with monotonic grayscale contrast only; "
                "source=https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
                "LDEM_80S_80MPP_ADJ_HILL.TIF; "
                + (
                    (
                        "depot and seven typed representative task sites copied "
                        "from the schematic-v5 logical layer; "
                    )
                    if args.schematic_v5_sites
                    else "task sites and depot only; "
                    if mission_summary is None
                    else (
                        "task sites, depot, and the instance reference solution's "
                        "feasible sortie geometry; route status is reference/NOT_SOLVED; "
                        "the rover is a schematic symbol rather than a real vehicle; "
                    )
                )
                + (
                    "all schematic-v5 sites use their instance coordinates."
                    if args.schematic_v5_sites
                    else "ice_site_006 has a presentation-only position override at (45, 41) km."
                )
            ),
        },
    )
    plt.close(fig)
    print(f"wrote {output_path}")
    print(
        f"instance_id={instance_id} task_count={len(tasks)} "
        f"depot_xy_km={depot_xy} cells={int(args.output_cells)}"
    )
    if mission_summary is not None:
        print(
            "mission_overlay="
            f"journey_{mission_summary['journey_index'] + 1}/"
            f"sortie_{mission_summary['sortie_index'] + 1} "
            f"tasks={','.join(mission_summary['tasks'])} "
            f"feasible={mission_summary['feasible']} "
            f"reference_exact_status={mission_summary['reference_exact_status']}"
        )
    return 0


def _draw_reference_mission_process(
    ax: plt.Axes,
    instance: dict[str, Any],
    *,
    journey_index: int,
    sortie_index: int,
) -> dict[str, Any]:
    """Overlay one data-backed feasible sortie using a schematic mission language."""
    reference = instance.get("reference_solution") or {}
    journeys = reference.get("journeys") or []
    if journey_index < 0 or journey_index >= len(journeys):
        raise IndexError(f"reference journey index out of range: {journey_index}")
    sorties = journeys[journey_index].get("sorties") or []
    if sortie_index < 0 or sortie_index >= len(sorties):
        raise IndexError(f"reference sortie index out of range: {sortie_index}")
    sortie = sorties[sortie_index]
    if not bool(sortie.get("feasible")):
        raise ValueError("the selected reference sortie is not marked feasible")

    edge_lookup = {
        (str(edge["from"]), str(edge["to"]), str(option["path_type"])): option
        for edge in instance["logical_graph"]["edges"]
        for option in edge.get("path_options", [])
    }
    leg_paths: list[tuple[dict[str, Any], np.ndarray]] = []
    for leg in sortie.get("legs", []):
        key = (
            str(leg["from"]),
            str(leg["to"]),
            str(leg.get("path_type", "low_risk")),
        )
        option = edge_lookup.get(key)
        if option is None:
            raise KeyError(f"missing path option for reference leg: {key}")
        points = np.asarray(option.get("path_xy", []), dtype="float64")
        if points.ndim != 2 or points.shape[0] < 2 or points.shape[1] != 2:
            raise ValueError(f"invalid path geometry for reference leg: {key}")
        leg_paths.append((leg, points))

    traverse_color = "#58a8bf"
    return_color = "#d7aa69"
    route_outline = "#101820"
    for leg_index, (leg, points) in enumerate(leg_paths):
        is_return = leg_index == len(leg_paths) - 1
        color = return_color if is_return else traverse_color
        linestyle = (0, (5.0, 3.0)) if is_return else "-"
        route_line = ax.plot(
            points[:, 0],
            points[:, 1],
            color=color,
            linewidth=2.9,
            linestyle=linestyle,
            solid_capstyle="round",
            dash_capstyle="round",
            alpha=0.97,
            zorder=4.1,
        )[0]
        route_line.set_path_effects(
            [
                path_effects.Stroke(
                    linewidth=5.2,
                    foreground=route_outline,
                    alpha=0.78,
                ),
                path_effects.Normal(),
            ]
        )
        _draw_direction_arrow(
            ax,
            points,
            color=color,
            outline_color=route_outline,
        )

    task_ids = [str(task_id) for task_id in sortie.get("tasks", [])]
    task_positions = {
        task_id: tuple(float(value) for value in instance["tasks"][task_id]["xy_km"])
        for task_id in task_ids
    }
    for task_id in task_ids:
        x, y = task_positions[task_id]
        ax.scatter(
            [x],
            [y],
            s=270,
            facecolors="none",
            edgecolors="#e8f1f2",
            linewidths=1.7,
            zorder=6.2,
        )

    depot_xy = tuple(float(value) for value in instance["depot"]["xy_km"])
    _draw_schematic_rover(ax, x=23.15, y=18.85, angle_deg=-24.0, size_km=2.2)

    _mission_callout(
        ax,
        xy=depot_xy,
        xytext=(28.0, 28.1),
        label="DEPARTURE\nfrom depot",
        number="1",
        accent=traverse_color,
    )
    first_xy = task_positions[task_ids[0]]
    _mission_callout(
        ax,
        xy=first_xy,
        xytext=(32.0, 5.2),
        label="SUBSURFACE\nICE DETECTION",
        number="2",
        accent=traverse_color,
    )
    _mission_callout(
        ax,
        xy=task_positions[task_ids[1]],
        xytext=(3.0, 32.2),
        label="PSR-BOUNDARY\nSURVEY",
        number="3",
        accent=traverse_color,
    )
    _mission_callout(
        ax,
        xy=task_positions[task_ids[-1]],
        xytext=(40.4, 12.9),
        label="MULTI-SITE\nVERIFICATION",
        number="4",
        accent=traverse_color,
    )

    return_points = leg_paths[-1][1]
    return_xy = _point_at_fraction(return_points, 0.50)
    _mission_callout(
        ax,
        xy=return_xy,
        xytext=(34.0, 25.8),
        label="LOW-ENERGY RETURN\n& RECHARGE",
        number="5",
        accent=return_color,
    )

    return {
        "journey_index": journey_index,
        "sortie_index": sortie_index,
        "tasks": task_ids,
        "feasible": bool(sortie.get("feasible")),
        "reference_exact_status": str(reference.get("exact_status", "UNKNOWN")),
    }


def _draw_direction_arrow(
    ax: plt.Axes,
    points: np.ndarray,
    *,
    color: str,
    outline_color: str,
) -> None:
    start = _point_at_fraction(points, 0.58)
    end = _point_at_fraction(points, 0.64)
    arrow = FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle="-|>",
        mutation_scale=18.0,
        linewidth=2.1,
        facecolor=color,
        edgecolor=color,
        shrinkA=0.0,
        shrinkB=0.0,
        zorder=4.6,
    )
    arrow.set_path_effects(
        [
            path_effects.Stroke(
                linewidth=4.1,
                foreground=outline_color,
                alpha=0.82,
            ),
            path_effects.Normal(),
        ]
    )
    ax.add_patch(arrow)


def _point_at_fraction(points: np.ndarray, fraction: float) -> tuple[float, float]:
    deltas = np.diff(points, axis=0)
    lengths = np.hypot(deltas[:, 0], deltas[:, 1])
    total = float(np.sum(lengths))
    if total <= 1.0e-12:
        return (float(points[0, 0]), float(points[0, 1]))
    target = float(np.clip(fraction, 0.0, 1.0)) * total
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    index = int(np.searchsorted(cumulative, target, side="right") - 1)
    index = min(max(index, 0), len(lengths) - 1)
    segment_length = float(lengths[index])
    ratio = 0.0 if segment_length <= 1.0e-12 else (target - cumulative[index]) / segment_length
    point = points[index] + ratio * deltas[index]
    return (float(point[0]), float(point[1]))


def _mission_callout(
    ax: plt.Axes,
    *,
    xy: tuple[float, float],
    xytext: tuple[float, float],
    label: str,
    number: str,
    accent: str,
) -> None:
    ax.annotate(
        f"{number}  {label}",
        xy=xy,
        xytext=xytext,
        textcoords="data",
        ha="left",
        va="center",
        fontsize=8.7,
        fontweight="semibold",
        linespacing=1.02,
        color="#101820",
        bbox={
            "boxstyle": "round,pad=0.38,rounding_size=0.18",
            "facecolor": "#f4f3ee",
            "edgecolor": accent,
            "linewidth": 1.35,
            "alpha": 0.94,
        },
        arrowprops={
            "arrowstyle": "-",
            "color": accent,
            "linewidth": 1.25,
            "shrinkA": 2.0,
            "shrinkB": 6.0,
            "connectionstyle": "arc3,rad=0.08",
        },
        zorder=9,
    )


def _draw_schematic_rover(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    angle_deg: float,
    size_km: float,
) -> None:
    """Draw a deliberately diagrammatic top-view rover glyph in data coordinates."""
    transform = Affine2D().rotate_deg_around(x, y, angle_deg) + ax.transData
    halo = Circle(
        (x, y),
        radius=0.78 * size_km,
        facecolor="#f4f3ee",
        edgecolor="#101820",
        linewidth=1.15,
        alpha=0.88,
        transform=transform,
        zorder=7.0,
    )
    ax.add_patch(halo)
    for center_y in (y - 0.37 * size_km, y + 0.37 * size_km):
        for center_x in (x - 0.42 * size_km, x, x + 0.42 * size_km):
            wheel = Circle(
                (center_x, center_y),
                radius=0.105 * size_km,
                facecolor="#101820",
                edgecolor="#f4f3ee",
                linewidth=0.55,
                transform=transform,
                zorder=7.5,
            )
            ax.add_patch(wheel)
    body = Rectangle(
        (x - 0.39 * size_km, y - 0.28 * size_km),
        0.78 * size_km,
        0.56 * size_km,
        facecolor="#d9e1e3",
        edgecolor="#101820",
        linewidth=1.15,
        transform=transform,
        zorder=7.7,
    )
    panel = Rectangle(
        (x - 0.29 * size_km, y - 0.20 * size_km),
        0.58 * size_km,
        0.40 * size_km,
        facecolor="#5e91a4",
        edgecolor="#f4f3ee",
        linewidth=0.65,
        hatch="++",
        transform=transform,
        zorder=7.9,
    )
    mast = Circle(
        (x + 0.08 * size_km, y),
        radius=0.105 * size_km,
        facecolor="#d7aa69",
        edgecolor="#101820",
        linewidth=0.85,
        transform=transform,
        zorder=8.1,
    )
    ax.add_patch(body)
    ax.add_patch(panel)
    ax.add_patch(mast)


def _build_official_lola_hillshade_rgb(
    *,
    official_hillshade: np.ndarray,
) -> np.ndarray:
    """Render the official LOLA hillshade without synthetic lighting fusion."""
    hillshade = np.flipud(np.asarray(official_hillshade, dtype="float64"))
    valid = np.isfinite(hillshade)
    luminance = _contrast_stretch(hillshade, lower=0.5, upper=99.5)
    luminance = np.power(luminance, 0.94)
    rgb = np.repeat(luminance[..., None], 3, axis=2)
    return np.dstack((rgb, valid.astype("float64")))


def _contrast_stretch(values: np.ndarray, *, lower: float, upper: float) -> np.ndarray:
    matrix = np.asarray(values, dtype="float64")
    finite = matrix[np.isfinite(matrix)]
    if finite.size == 0:
        raise ValueError("cannot stretch a raster without finite values")
    low, high = (float(value) for value in np.percentile(finite, (lower, upper)))
    if high <= low + 1.0e-12:
        raise ValueError("degenerate raster contrast range")
    return np.clip((matrix - low) / (high - low), 0.0, 1.0)


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


if __name__ == "__main__":
    raise SystemExit(main())

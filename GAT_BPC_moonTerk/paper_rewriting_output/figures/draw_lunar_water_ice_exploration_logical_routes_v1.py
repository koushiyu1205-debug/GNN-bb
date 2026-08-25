#!/usr/bin/env python3
"""Draw the standalone logical-routing layer from the v5 lunar schematic.

The minimalist network styling follows the supplied published-figure example:
numbered task nodes, a square depot, thin directional routes, and a compact
line-style key.  Coordinates and trip membership are inherited from v5.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np

from draw_lunar_water_ice_exploration_schematic_v5 import (
    INSTANCE_PATH,
    TASK_MARKERS,
    V5_LOGICAL_TRIPS,
    VEHICLE_COLORS,
    configure_scientific_style,
    read_json,
)


FIGURE_DIR = Path(__file__).resolve().parent
OUTPUT_PNG_PATH = FIGURE_DIR / "lunar_water_ice_exploration_logical_routes_v1.png"
OUTPUT_PDF_PATH = FIGURE_DIR / "lunar_water_ice_exploration_logical_routes_v1.pdf"
OUTPUT_DPI = 500

INK = "#11181D"
MUTED_INK = "#4F5B62"
CANDIDATE_COLOR = "#78858C"
TASK_FACE = "#FFC928"


def _draw_straight_route(
    ax: plt.Axes,
    *,
    start: np.ndarray,
    end: np.ndarray,
    color: str,
    curvature: float = 0.0,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            tuple(start),
            tuple(end),
            arrowstyle="-|>",
            mutation_scale=10.5,
            linewidth=1.75,
            color=color,
            shrinkA=11.0,
            shrinkB=12.0,
            connectionstyle=f"arc3,rad={curvature:.3f}",
            capstyle="round",
            joinstyle="round",
            zorder=4,
        )
    )


def _draw_candidate_route(
    ax: plt.Axes,
    *,
    start: np.ndarray,
    end: np.ndarray,
    curvature: float,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            tuple(start),
            tuple(end),
            arrowstyle="-|>",
            mutation_scale=8.2,
            linewidth=1.08,
            linestyle=(0, (4.0, 3.0)),
            color=CANDIDATE_COLOR,
            alpha=0.82,
            shrinkA=13.0,
            shrinkB=14.0,
            connectionstyle=f"arc3,rad={curvature:.3f}",
            capstyle="round",
            joinstyle="round",
            zorder=2,
        )
    )


def _draw_task_nodes(
    ax: plt.Axes,
    *,
    instance: dict,
    task_number_by_id: dict[str, int],
    positions: dict[str, np.ndarray],
) -> None:
    for task_id, task_number in task_number_by_id.items():
        x, y = (float(value) for value in positions[task_id])
        operation_mode = str(instance["tasks"][task_id]["operation_mode"])
        marker = TASK_MARKERS[operation_mode]
        marker_size = 235 if operation_mode == "sample" else 220
        ax.scatter(
            [x],
            [y],
            s=marker_size,
            marker=marker,
            facecolor=TASK_FACE,
            edgecolor=INK,
            linewidth=1.15,
            zorder=7,
        )
        ax.text(
            x,
            y - 0.22 if operation_mode == "sample" else y,
            str(task_number),
            ha="center",
            va="center",
            fontsize=10.8,
            color=INK,
            zorder=8,
        )


def _draw_depot(ax: plt.Axes, *, center: np.ndarray) -> None:
    x, y = (float(value) for value in center)
    ax.scatter(
        [x],
        [y],
        s=720,
        marker="*",
        facecolor="white",
        edgecolor=INK,
        linewidth=1.2,
        zorder=9,
    )
    ax.text(
        x,
        y,
        "0",
        ha="center",
        va="center",
        fontsize=10.8,
        color=INK,
        bbox={
            "boxstyle": "circle,pad=0.04",
            "facecolor": "white",
            "edgecolor": "none",
        },
        zorder=11,
    )


def _draw_trip_label(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    vehicle: str,
    trip_number: int,
) -> None:
    color = VEHICLE_COLORS[vehicle]
    ax.text(
        x,
        y,
        f"{vehicle}, trip {trip_number}",
        ha="center",
        va="center",
        fontsize=10.8,
        color=color,
        fontweight="semibold",
        bbox={
            "boxstyle": "round,pad=0.18,rounding_size=0.12",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.92,
        },
        zorder=11,
    )


def _draw_style_key(ax: plt.Axes) -> None:
    x0, y0 = 32.6, 39.0
    width, height = 18.7, 11.5
    ax.add_patch(
        Rectangle(
            (x0, y0),
            width,
            height,
            facecolor="white",
            edgecolor=INK,
            linewidth=0.75,
            zorder=20,
        )
    )
    selected_y = y0 + 9.10
    candidate_y = y0 + 6.75
    ax.add_patch(
        FancyArrowPatch(
            (x0 + 1.1, selected_y),
            (x0 + 4.3, selected_y),
            arrowstyle="-|>",
            mutation_scale=7.8,
            linewidth=1.05,
            color=MUTED_INK,
            shrinkA=0.0,
            shrinkB=0.0,
            zorder=21,
        )
    )
    ax.text(
        x0 + 4.95,
        selected_y,
        "selected path",
        fontsize=9.0,
        color=INK,
        va="center",
        zorder=21,
    )
    ax.add_patch(
        FancyArrowPatch(
            (x0 + 1.1, candidate_y + 0.34),
            (x0 + 4.3, candidate_y + 0.34),
            arrowstyle="-|>",
            mutation_scale=7.5,
            linewidth=1.0,
            linestyle=(0, (4.0, 3.0)),
            color=CANDIDATE_COLOR,
            shrinkA=0.0,
            shrinkB=0.0,
            connectionstyle="arc3,rad=-0.20",
            zorder=21,
        )
    )
    ax.add_patch(
        FancyArrowPatch(
            (x0 + 1.1, candidate_y - 0.34),
            (x0 + 4.3, candidate_y - 0.34),
            arrowstyle="-|>",
            mutation_scale=7.5,
            linewidth=1.0,
            linestyle=(0, (4.0, 3.0)),
            color=CANDIDATE_COLOR,
            shrinkA=0.0,
            shrinkB=0.0,
            connectionstyle="arc3,rad=0.20",
            zorder=21,
        )
    )
    ax.text(
        x0 + 4.95,
        candidate_y,
        "unselected\ncandidate paths",
        fontsize=9.0,
        color=INK,
        va="center",
        linespacing=0.95,
        zorder=21,
    )

    task_items = (
        (x0 + 1.45, y0 + 3.45, "detect", "detection"),
        (x0 + 9.85, y0 + 3.45, "sample", "sampling"),
        (x0 + 1.45, y0 + 1.25, "drill", "drilling"),
    )
    for x, y, mode, label in task_items:
        ax.scatter(
            [x],
            [y],
            s=70 if mode != "sample" else 78,
            marker=TASK_MARKERS[mode],
            facecolor=TASK_FACE,
            edgecolor=INK,
            linewidth=0.8,
            zorder=21,
        )
        ax.text(
            x + 1.15,
            y,
            label,
            fontsize=8.8,
            color=INK,
            va="center",
            zorder=21,
        )


def main() -> int:
    instance = read_json(INSTANCE_PATH)
    depot_id = str(instance["depot"]["id"])
    trips = [dict(spec) for spec in V5_LOGICAL_TRIPS]
    selected_task_ids = {
        task_id
        for trip in trips
        for task_id in trip["task_ids"]
    }
    ordered_task_ids = sorted(
        selected_task_ids,
        key=lambda task_id: int(task_id.rsplit("_", maxsplit=1)[1]),
    )
    task_number_by_id = {
        task_id: index
        for index, task_id in enumerate(ordered_task_ids, start=1)
    }
    positions = {
        depot_id: np.asarray(instance["depot"]["xy_km"], dtype="float64"),
        **{
            task_id: np.asarray(instance["tasks"][task_id]["xy_km"], dtype="float64")
            for task_id in selected_task_ids
        },
    }

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": OUTPUT_DPI,
            "font.family": "DejaVu Serif",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    figure, ax = plt.subplots(figsize=(8.8, 6.6), facecolor="white")

    candidate_curvatures = (0.18, -0.16, 0.20, -0.18)
    for trip_index, trip in enumerate(trips):
        vehicle = str(trip["vehicle"])
        color = VEHICLE_COLORS[vehicle]
        sequence = (depot_id, *trip["task_ids"], depot_id)
        single_task_trip = len(trip["task_ids"]) == 1
        for leg_index, (source, target) in enumerate(zip(sequence, sequence[1:])):
            start = positions[str(source)]
            end = positions[str(target)]
            is_return = leg_index == len(sequence) - 2
            curvature = abs(candidate_curvatures[trip_index])
            if single_task_trip:
                curvature = 0.23 if not is_return else 0.36
            elif leg_index % 2:
                curvature *= 1.08
            for candidate_curvature in (curvature, -curvature):
                _draw_candidate_route(
                    ax,
                    start=start,
                    end=end,
                    curvature=candidate_curvature,
                )
            _draw_straight_route(
                ax,
                start=start,
                end=end,
                color=color,
                curvature=0.115 if single_task_trip else 0.0,
            )

    _draw_task_nodes(
        ax,
        instance=instance,
        task_number_by_id=task_number_by_id,
        positions=positions,
    )
    _draw_depot(ax, center=positions[depot_id])

    trip_label_positions = {
        ("V1", 1): (14.0, 48.2),
        ("V1", 2): (42.2, 31.0),
        ("V2", 1): (38.0, 3.0),
        ("V3", 1): (9.5, 24.0),
    }
    for trip in trips:
        vehicle = str(trip["vehicle"])
        trip_number = int(trip["trip"])
        label_x, label_y = trip_label_positions[(vehicle, trip_number)]
        _draw_trip_label(
            ax,
            x=label_x,
            y=label_y,
            vehicle=vehicle,
            trip_number=trip_number,
        )

    _draw_style_key(ax)
    ax.set_xlim(-1.5, 52.0)
    ax.set_ylim(-1.5, 52.0)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    metadata = {
        "Title": "Lunar water-ice exploration logical routing diagram",
        "Subject": "Four illustrative closed trips over one depot and seven representative tasks",
        "Keywords": "lunar routing, multi-trip route, candidate path, depot",
    }
    figure.savefig(
        OUTPUT_PNG_PATH,
        dpi=OUTPUT_DPI,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={"Software": "Matplotlib"},
    )
    figure.savefig(
        OUTPUT_PDF_PATH,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata=metadata,
    )
    plt.close(figure)

    print(f"wrote {OUTPUT_PNG_PATH}")
    print(f"wrote {OUTPUT_PDF_PATH}")
    print(f"depot={depot_id}:0")
    for task_id in ordered_task_ids:
        print(f"task_{task_number_by_id[task_id]}={task_id}")
    print("vehicle_trip_count=V1:2,V2:1,V3:1")
    print("selected_path=solid_vehicle_color")
    print("unselected_candidate_paths=two_dashed_curved_gray_per_directed_leg")
    print("selection_semantics=illustrative; not solver output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

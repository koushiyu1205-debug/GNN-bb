#!/usr/bin/env python3
"""Draw a journal-style concept diagram of the lunar routing model.

The composition follows the supplied stage-wise reference figure while keeping
model semantics separate from the BPC and learning algorithms. It summarizes
mission tasks, environment layers, local-path alternatives, multi-trip route
feasibility, and fleet-plan evaluation.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np

from draw_lunar_water_ice_exploration_schematic_v5 import (
    INSTANCE_PATH,
    TASK_MARKERS,
    VEHICLE_COLORS,
    configure_scientific_style,
    read_json,
)


FIGURE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT_PANEL_PATH = (
    ROOT
    / "output/data_figures/lunar_sp50_020_instance_001_environment_panels_no_sites.png"
)
OUTPUT_PNG_PATH = FIGURE_DIR / "lunar_water_ice_exploration_model_concept_v1.png"
OUTPUT_PDF_PATH = FIGURE_DIR / "lunar_water_ice_exploration_model_concept_v1.pdf"
OUTPUT_DPI = 500

INK = "#172126"
MUTED = "#5A666D"
LIGHT_EDGE = "#AEB8BD"
PANEL_FACE = "#FBFCFC"
HEADER_FACE = "#EDF1F3"
ACCENT_RED = "#D62728"
TASK_FACE = "#FFC928"
PATH_COLORS = {
    "time": "#3E78B2",
    "energy": "#D79A24",
    "risk": "#B04A7A",
}


TOP_X = (0.015, 0.211, 0.407, 0.603, 0.799)
TOP_Y = 0.600
TOP_W = 0.174
TOP_H = 0.280
BOTTOM_Y = 0.065
BOTTOM_H = 0.400


def _load_environment_thumbnails() -> dict[str, np.ndarray]:
    """Crop the four map panels without titles, axes, or color bars."""
    image = np.asarray(plt.imread(ENVIRONMENT_PANEL_PATH), dtype="float64")[..., :3]
    height, width = image.shape[:2]
    y_top = slice(int(round(0.045 * height)), int(round(0.446 * height)))
    y_bottom = slice(int(round(0.523 * height)), int(round(0.910 * height)))
    x_left = slice(int(round(0.060 * width)), int(round(0.389 * width)))
    x_right = slice(int(round(0.558 * width)), int(round(0.886 * width)))
    return {
        "dem": image[y_top, x_left],
        "illumination": image[y_top, x_right],
        "risk": image[y_bottom, x_left],
        "roughness": image[y_bottom, x_right],
    }


def _load_light_terrain_thumbnail() -> np.ndarray:
    crop = _load_environment_thumbnails()["roughness"]
    gray = (
        0.2126 * crop[..., 0]
        + 0.7152 * crop[..., 1]
        + 0.0722 * crop[..., 2]
    )
    low, high = np.nanpercentile(gray, (2.0, 98.0))
    normalized = np.clip((gray - low) / max(high - low, 1.0e-12), 0.0, 1.0)
    light = 0.68 + 0.28 * normalized
    return np.repeat(light[..., None], 3, axis=2)


def _style_panel(ax: plt.Axes) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor(PANEL_FACE)
    for spine in ax.spines.values():
        spine.set_color("#59646A")
        spine.set_linewidth(0.85)


def _task_marker(
    ax: plt.Axes,
    x: float,
    y: float,
    *,
    mode: str,
    size: float = 105.0,
    label: str | None = None,
    label_fontsize: float = 9.2,
    alpha: float = 1.0,
    zorder: int = 8,
) -> None:
    ax.scatter(
        [x],
        [y],
        s=size,
        marker=TASK_MARKERS[mode],
        facecolor=TASK_FACE,
        edgecolor=INK,
        linewidth=0.85,
        alpha=alpha,
        zorder=zorder,
    )
    if label:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=label_fontsize,
            fontweight="semibold",
            color=INK,
            zorder=zorder + 1,
        )


def _depot_marker(
    ax: plt.Axes,
    x: float,
    y: float,
    *,
    size: float = 220.0,
    label: str | None = "0",
    label_fontsize: float = 9.4,
    zorder: int = 10,
) -> None:
    ax.scatter(
        [x],
        [y],
        s=size,
        marker="*",
        facecolor="#FFF1A8",
        edgecolor=INK,
        linewidth=1.0,
        zorder=zorder,
    )
    if label:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=label_fontsize,
            fontweight="semibold",
            color=INK,
            zorder=zorder + 1,
        )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    linewidth: float = 1.7,
    curvature: float = 0.0,
    dashed: bool = False,
    zorder: int = 5,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=9.5,
            linewidth=linewidth,
            color=color,
            linestyle=(0, (3.2, 2.4)) if dashed else "-",
            shrinkA=5.0,
            shrinkB=6.0,
            connectionstyle=f"arc3,rad={curvature:.3f}",
            capstyle="round",
            joinstyle="round",
            zorder=zorder,
        )
    )


def _draw_panel_1(ax: plt.Axes, *, instance: dict, terrain: np.ndarray) -> None:
    _style_panel(ax)
    ax.imshow(terrain, extent=(0.0, 1.0, 0.0, 1.0), origin="upper", zorder=0)
    ax.text(
        0.04,
        0.95,
        r"$50\,\mathrm{km}\times50\,\mathrm{km}$",
        fontsize=10.2,
        color=INK,
        ha="left",
        va="top",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.5},
        zorder=12,
    )
    task_ids = (
        "ice_site_001",
        "ice_site_003",
        "ice_site_004",
        "ice_site_006",
        "ice_site_007",
        "ice_site_009",
        "ice_site_018",
    )
    for number, task_id in enumerate(task_ids, start=1):
        task = instance["tasks"][task_id]
        x_km, y_km = (float(value) for value in task["xy_km"])
        x = 0.08 + 0.84 * x_km / 50.0
        y = 0.08 + 0.84 * y_km / 50.0
        _task_marker(
            ax,
            x,
            y,
            mode=str(task["operation_mode"]),
            size=138.0,
            label=str(number),
            label_fontsize=7.5,
        )
    _depot_marker(ax, 0.50, 0.50, size=245.0, label_fontsize=7.5)


def _draw_panel_2(ax: plt.Axes, *, maps: dict[str, np.ndarray]) -> None:
    """Show the lunar environment as three aligned planning layers."""
    _style_panel(ax)
    layers = (
        ("dem", "terrain", 0.68),
        ("illumination", "illumination / shadow", 0.375),
        ("risk", "traversal risk", 0.070),
    )
    for key, label, y0 in layers:
        ax.imshow(maps[key], extent=(0.08, 0.92, y0, y0 + 0.235), origin="upper", zorder=1)
        ax.add_patch(Rectangle((0.08, y0), 0.84, 0.235, fill=False, edgecolor="white", linewidth=0.8, zorder=3))
        ax.text(
            0.11,
            y0 + 0.195,
            label,
            fontsize=9.8,
            color=INK,
            ha="left",
            va="center",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.8},
            zorder=4,
        )


def _draw_panel_3(ax: plt.Axes, *, terrain: np.ndarray) -> None:
    """Show heterogeneous local paths between a directed node pair."""
    _style_panel(ax)
    ax.imshow(terrain, extent=(0.0, 1.0, 0.0, 1.0), origin="upper", alpha=0.32, zorder=0)
    source = (0.19, 0.30)
    target = (0.82, 0.72)
    _task_marker(ax, *source, mode="detect", size=132.0, label="i", label_fontsize=7.8)
    _task_marker(ax, *target, mode="sample", size=142.0, label="j", label_fontsize=7.8)
    path_specs = (
        ("time", -0.24, "low time", 0.83),
        ("energy", 0.00, "low energy", 0.49),
        ("risk", 0.24, "low risk", 0.20),
    )
    for key, curvature, label, label_y in path_specs:
        _arrow(ax, source, target, color=PATH_COLORS[key], linewidth=1.65, curvature=curvature)
        ax.text(
            0.56,
            label_y,
            label,
            fontsize=9.8,
            color=PATH_COLORS[key],
            ha="center",
            va="center",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.7},
            zorder=12,
        )


def _draw_panel_4(ax: plt.Axes) -> None:
    """Show consecutive depot-to-depot trips for one rover."""
    _style_panel(ax)
    color = VEHICLE_COLORS["V1"]
    depot = (0.50, 0.46)
    trip_1 = ((0.15, 0.73), (0.39, 0.84))
    trip_2 = ((0.84, 0.72), (0.78, 0.24))
    _depot_marker(ax, *depot, size=230.0, label_fontsize=7.5)
    _task_marker(ax, *trip_1[0], mode="detect", size=82.0)
    _task_marker(ax, *trip_1[1], mode="sample", size=90.0)
    _task_marker(ax, *trip_2[0], mode="drill", size=82.0)
    _task_marker(ax, *trip_2[1], mode="sample", size=90.0)
    for start, end in (
        (depot, trip_1[0]),
        (trip_1[0], trip_1[1]),
        (trip_1[1], depot),
        (depot, trip_2[0]),
        (trip_2[0], trip_2[1]),
        (trip_2[1], depot),
    ):
        _arrow(ax, start, end, color=color, linewidth=1.65)
    ax.text(0.15, 0.92, "trip 1", fontsize=9.8, color=color, fontweight="semibold")
    ax.text(0.70, 0.92, "trip 2", fontsize=9.8, color=color, fontweight="semibold")
    ax.text(
        0.50,
        0.105,
        "return · recharge",
        fontsize=9.8,
        color=INK,
        ha="center",
        va="center",
        bbox={"facecolor": "white", "edgecolor": LIGHT_EDGE, "linewidth": 0.6, "pad": 1.5},
        zorder=10,
    )


def _draw_panel_5(ax: plt.Axes) -> None:
    """Show task allocation and the three normalized objective components."""
    _style_panel(ax)
    rows = (
        (0.82, "V1", VEHICLE_COLORS["V1"], ("1", "3", "6")),
        (0.66, "V2", VEHICLE_COLORS["V2"], ("2", "5")),
        (0.50, "V3", VEHICLE_COLORS["V3"], ("4", "7")),
    )
    task_modes = {
        "1": "drill",
        "2": "detect",
        "3": "sample",
        "4": "detect",
        "5": "drill",
        "6": "sample",
        "7": "sample",
    }
    for y, vehicle, color, task_numbers in rows:
        ax.text(0.07, y, vehicle, fontsize=9.8, color=color, fontweight="semibold", va="center")
        ax.plot([0.23, 0.40], [y, y], color=color, linewidth=2.0, solid_capstyle="round")
        for offset, task_number in enumerate(task_numbers):
            x = 0.54 + 0.14 * offset
            ax.scatter([x], [y], s=96, marker=TASK_MARKERS[task_modes[task_number]], facecolor=TASK_FACE, edgecolor=INK, linewidth=0.75)
            ax.text(x, y, task_number, fontsize=7.3, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text(0.50, 0.945, "each task once", fontsize=9.8, color=INK, ha="center", va="center")
    objective_rows = (
        (0.34, "cost", "#4C78A8", 0.70, ""),
        (0.22, "risk", "#D95F5F", 0.48, ""),
        (0.10, "weighted time", "#E3B341", 0.60, "0.4"),
    )
    for y, label, color, fraction, badge in objective_rows:
        ax.text(0.07, y, label, fontsize=8.9, color=INK, ha="left", va="center")
        ax.add_patch(Rectangle((0.62, y - 0.025), 0.30, 0.05, facecolor="#E8ECEE", edgecolor="none"))
        ax.add_patch(Rectangle((0.62, y - 0.025), 0.30 * fraction, 0.05, facecolor=color, edgecolor="none"))
        if badge:
            ax.text(0.77, y, badge, fontsize=8.6, color=INK, ha="center", va="center")


def _bottom_box(ax: plt.Axes, *, title: str) -> None:
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.add_patch(
        Rectangle(
            (0.0, 0.0),
            1.0,
            1.0,
            facecolor="white",
            edgecolor=LIGHT_EDGE,
            linewidth=0.8,
        )
    )
    ax.add_patch(
        Rectangle(
            (0.0, 0.82),
            1.0,
            0.18,
            facecolor=HEADER_FACE,
            edgecolor=LIGHT_EDGE,
            linewidth=0.8,
        )
    )
    ax.text(
        0.50,
        0.91,
        title,
        fontsize=10.2,
        fontweight="semibold",
        color=INK,
        ha="center",
        va="center",
    )


def _pill(ax: plt.Axes, x: float, y: float, width: float, text: str, *, face: str = "#F3F6F7") -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x - width / 2.0, y - 0.042),
            width,
            0.084,
            boxstyle="round,pad=0.006,rounding_size=0.018",
            facecolor=face,
            edgecolor=LIGHT_EDGE,
            linewidth=0.55,
        )
    )
    ax.text(x, y, text, fontsize=9.4, color=INK, ha="center", va="center")


def _draw_rover_icon(ax: plt.Axes, x: float, y: float, *, color: str, scale: float = 1.0) -> None:
    width = 0.12 * scale
    height = 0.055 * scale
    ax.add_patch(Rectangle((x - width / 2, y - height / 2), width, height, facecolor=color, edgecolor=INK, linewidth=0.55))
    ax.plot([x, x + 0.035 * scale], [y + height / 2, y + height / 2 + 0.045 * scale], color=INK, linewidth=0.7)
    ax.add_patch(Rectangle((x + 0.022 * scale, y + height / 2 + 0.035 * scale), 0.055 * scale, 0.025 * scale, facecolor="#C9D9E4", edgecolor=INK, linewidth=0.45))
    for wheel_x in (x - 0.035 * scale, x + 0.035 * scale):
        ax.add_patch(Circle((wheel_x, y - height / 2 - 0.012 * scale), 0.018 * scale, facecolor=INK, edgecolor="none"))


def _draw_clock_icon(ax: plt.Axes, x: float, y: float, *, radius: float = 0.055) -> None:
    ax.add_patch(Circle((x, y), radius, facecolor="white", edgecolor=INK, linewidth=0.7))
    ax.plot([x, x], [y, y + 0.032], color=INK, linewidth=0.8)
    ax.plot([x, x + 0.030], [y, y - 0.018], color=INK, linewidth=0.8)


def _draw_gauge(ax: plt.Axes, x: float, y: float, label: str, fraction: float, color: str) -> None:
    ax.text(x, y + 0.047, label, fontsize=9.2, color=MUTED, ha="center", va="center")
    ax.add_patch(Rectangle((x - 0.105, y - 0.020), 0.210, 0.040, facecolor="#E5EAEC", edgecolor=LIGHT_EDGE, linewidth=0.45))
    ax.add_patch(Rectangle((x - 0.105, y - 0.020), 0.210 * fraction, 0.040, facecolor=color, edgecolor="none"))


def _draw_bottom_1(ax: plt.Axes) -> None:
    _bottom_box(ax, title="Task and fleet data")
    for y in (0.63, 0.48, 0.33, 0.18):
        ax.plot([0.04, 0.96], [y, y], color="#E1E5E7", linewidth=0.55)
    labels = ((0.71, "operation"), (0.56, "science value"), (0.41, "service demand"), (0.26, "time window"), (0.11, "fleet"))
    for y, label in labels:
        ax.text(0.05, y, label, fontsize=9.2, color=MUTED, ha="left", va="center")

    for x, mode in ((0.47, "detect"), (0.67, "sample"), (0.87, "drill")):
        _task_marker(ax, x, 0.73, mode=mode, size=68.0)

    priority_colors = ("#DDE5EA", "#B8CAD5", "#84A9BF", "#4C78A8")
    for index, color in enumerate(priority_colors):
        ax.add_patch(Rectangle((0.43 + 0.115 * index, 0.525), 0.075, 0.065, facecolor=color, edgecolor="white", linewidth=0.4))

    for index, width in enumerate((0.15, 0.24, 0.33)):
        y = 0.445 - 0.035 * index
        ax.plot([0.48, 0.48 + width], [y, y], color="#52656F", linewidth=2.0, solid_capstyle="butt")

    ax.plot([0.43, 0.91], [0.26, 0.26], color="#869197", linewidth=0.75)
    for x0, x1 in ((0.47, 0.66), (0.72, 0.88)):
        ax.plot([x0, x1], [0.26, 0.26], color="#4C78A8", linewidth=3.0)
        ax.plot([x0, x0], [0.235, 0.285], color="#4C78A8", linewidth=0.7)
        ax.plot([x1, x1], [0.235, 0.285], color="#4C78A8", linewidth=0.7)

    _depot_marker(ax, 0.44, 0.11, size=125.0, label=None)
    for index, (vehicle, color) in enumerate((("V1", VEHICLE_COLORS["V1"]), ("V2", VEHICLE_COLORS["V2"]), ("V3", VEHICLE_COLORS["V3"]))):
        x0 = 0.56 + 0.13 * index
        ax.plot([x0, x0 + 0.07], [0.11, 0.11], color=color, linewidth=2.2)
        ax.text(x0 + 0.035, 0.065, vehicle, fontsize=8.8, color=color, ha="center", va="center")


def _draw_bottom_2(ax: plt.Axes, *, maps: dict[str, np.ndarray]) -> None:
    _bottom_box(ax, title="Layer synthesis")
    cards = (
        (0.05, "dem", "terrain"),
        (0.375, "illumination", "shadow"),
        (0.70, "risk", "risk"),
    )
    for x0, key, label in cards:
        ax.imshow(maps[key], extent=(x0, x0 + 0.25, 0.57, 0.74), origin="upper", zorder=1)
        ax.add_patch(Rectangle((x0, 0.57), 0.25, 0.17, fill=False, edgecolor=LIGHT_EDGE, linewidth=0.55, zorder=2))
        ax.text(x0 + 0.125, 0.525, label, fontsize=9.2, color=INK, ha="center", va="center")
        _arrow(ax, (x0 + 0.125, 0.49), (0.50, 0.39), color="#78848A", linewidth=0.7, curvature=0.0)
    composite_extent = (0.29, 0.71, 0.18, 0.36)
    ax.imshow(maps["dem"], extent=composite_extent, origin="upper", zorder=1)
    ax.imshow(maps["illumination"], extent=composite_extent, origin="upper", alpha=0.30, zorder=2)
    ax.imshow(maps["risk"], extent=composite_extent, origin="upper", alpha=0.22, zorder=3)
    ax.add_patch(Rectangle((0.29, 0.18), 0.42, 0.18, fill=False, edgecolor="#59646A", linewidth=0.65, zorder=4))
    ax.text(0.50, 0.125, "integrated path map", fontsize=9.6, color=INK, ha="center", va="center")
    ax.plot([0.22, 0.78], [0.072, 0.072], color=LIGHT_EDGE, linewidth=0.55)
    ax.text(0.50, 0.035, "fixed operational phase", fontsize=9.1, color=MUTED, ha="center", va="center")


def _draw_bottom_3(ax: plt.Axes) -> None:
    _bottom_box(ax, title="Path alternatives")
    source = (0.15, 0.67)
    target = (0.85, 0.67)
    _task_marker(ax, *source, mode="detect", size=40.0)
    _task_marker(ax, *target, mode="sample", size=44.0)
    for color, curvature in ((PATH_COLORS["time"], -0.24), (PATH_COLORS["energy"], 0.0), (PATH_COLORS["risk"], 0.24)):
        _arrow(ax, source, target, color=color, linewidth=1.35, curvature=curvature)
    columns = ((0.43, "time"), (0.57, "energy"), (0.71, "shadow"), (0.85, "risk"))
    for x, label in columns:
        ax.text(x - 0.015, 0.445, label, fontsize=8.3, color=MUTED, ha="left", va="bottom", rotation=52)
    row_colors = (PATH_COLORS["time"], PATH_COLORS["energy"], PATH_COLORS["risk"])
    for row, color in enumerate(row_colors):
        y = 0.365 - 0.095 * row
        ax.plot([0.10, 0.25], [y, y], color=color, linewidth=2.0)
        ax.text(0.30, y, f"P{row + 1}", fontsize=9.0, color=INK, ha="center", va="center")
        for col, (x, _) in enumerate(columns):
            ax.add_patch(Rectangle((x - 0.045, y - 0.035), 0.09, 0.07, facecolor="#F2F5F6", edgecolor=LIGHT_EDGE, linewidth=0.45))
            accent = (row == 0 and col == 0) or (row == 1 and col == 1) or (row == 2 and col == 3)
            ax.add_patch(Circle((x, y), 0.016, facecolor=color if accent else "#AAB4B9", edgecolor="none"))
    ax.text(0.50, 0.055, "candidate attribute records", fontsize=9.4, color=INK, ha="center", va="center")


def _draw_bottom_4(ax: plt.Axes) -> None:
    _bottom_box(ax, title="Feasibility assembly")
    depot = (0.12, 0.68)
    tasks = ((0.36, 0.72, "detect"), (0.61, 0.64, "sample"), (0.86, 0.70, "drill"))
    _depot_marker(ax, *depot, size=125.0, label=None)
    previous = depot
    for x, y, mode in tasks:
        _task_marker(ax, x, y, mode=mode, size=65.0)
        _arrow(ax, previous, (x, y), color=VEHICLE_COLORS["V1"], linewidth=1.25)
        previous = (x, y)
    _arrow(ax, previous, depot, color=VEHICLE_COLORS["V1"], linewidth=1.25, curvature=0.24)
    for x, label, fraction, color in (
        (0.20, "load", 0.62, "#4C78A8"),
        (0.50, "energy", 0.70, "#E3B341"),
        (0.80, "shadow", 0.55, "#667F9E"),
    ):
        _draw_gauge(ax, x, 0.43, label, fraction, color)
    ax.plot([0.10, 0.90], [0.145, 0.145], color="#59646A", linewidth=0.8)
    _arrow(ax, (0.86, 0.145), (0.93, 0.145), color="#59646A", linewidth=0.8)
    events = (
        (0.17, "depot\nrelease", VEHICLE_COLORS["V1"], 0.058),
        (0.50, "arrival and\nservice start", "#27824A", 0.235),
        (0.83, "return and\nrecharge", "#C68B00", 0.058),
    )
    for x, label, color, label_y in events:
        ax.plot([x, x], [0.115, 0.185], color=color, linewidth=1.2)
        ax.scatter([x], [0.145], s=22, facecolor="white", edgecolor=color, linewidth=0.8, zorder=3)
        ax.text(x, label_y, label, fontsize=8.6, color=INK, ha="center", va="center", linespacing=0.95)


def _draw_bottom_5(ax: plt.Axes) -> None:
    _bottom_box(ax, title="Fleet-plan selection")
    ax.text(0.50, 0.755, "feasible route pool", fontsize=9.4, color=MUTED, ha="center", va="center")
    for index, color in enumerate((VEHICLE_COLORS["V1"], VEHICLE_COLORS["V2"], VEHICLE_COLORS["V3"])):
        x0 = 0.12 + 0.27 * index
        ax.add_patch(Rectangle((x0, 0.59), 0.22, 0.12, facecolor="white", edgecolor=LIGHT_EDGE, linewidth=0.55))
        ax.plot([x0 + 0.035, x0 + 0.18], [0.65, 0.65], color=color, linewidth=1.7)
        ax.scatter([x0 + 0.06, x0 + 0.16], [0.65, 0.65], s=13, color=TASK_FACE, edgecolor=INK, linewidth=0.35, zorder=3)
    _arrow(ax, (0.50, 0.57), (0.50, 0.51), color="#78848A", linewidth=0.75)
    ax.text(0.50, 0.545, "exact task cover", fontsize=9.4, color=INK, ha="center", va="center")
    x0, y0, cell_w, cell_h = 0.28, 0.29, 0.11, 0.052
    for row in range(4):
        for col in range(4):
            ax.add_patch(Rectangle((x0 + col * cell_w, y0 + row * cell_h), cell_w, cell_h, facecolor="#F5F7F8", edgecolor=LIGHT_EDGE, linewidth=0.35))
    for row, col in enumerate((0, 2, 1, 3)):
        ax.text(x0 + (col + 0.5) * cell_w, y0 + (row + 0.5) * cell_h, "✓", fontsize=9.5, color="#27824A", ha="center", va="center")
    _arrow(ax, (0.50, 0.26), (0.50, 0.20), color="#78848A", linewidth=0.75)
    bar_x, bar_y, bar_w, bar_h = 0.17, 0.10, 0.66, 0.07
    segments = ((0.36, "#4C78A8"), (0.28, "#D95F5F"), (0.36, "#E3B341"))
    cursor = bar_x
    for fraction, color in segments:
        width = bar_w * fraction
        ax.add_patch(Rectangle((cursor, bar_y), width, bar_h, facecolor=color, edgecolor="white", linewidth=0.45))
        cursor += width
    ax.text(0.71, bar_y + bar_h / 2.0, "0.4", fontsize=8.8, color=INK, ha="center", va="center")
    for x, label in ((0.29, "cost"), (0.50, "risk"), (0.71, "time")):
        ax.text(x, 0.055, label, fontsize=8.9, color=INK, ha="center", va="center")


def _algorithm_module(ax: plt.Axes, x0: float, x1: float, title: str) -> None:
    ax.add_patch(Rectangle((x0, 0.27), x1 - x0, 0.54, facecolor="white", edgecolor=LIGHT_EDGE, linewidth=0.65))
    ax.add_patch(Rectangle((x0, 0.70), x1 - x0, 0.11, facecolor=HEADER_FACE, edgecolor=LIGHT_EDGE, linewidth=0.65))
    ax.text((x0 + x1) / 2.0, 0.755, title, fontsize=9.7, fontweight="semibold", color=INK, ha="center", va="center")


def _draw_algorithm_workflow(ax: plt.Axes) -> None:
    """Draw a restrained two-stage flowchart in the style of TRC method figures."""
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.add_patch(Rectangle((0.0, 0.0), 1.0, 1.0, facecolor="white", edgecolor=LIGHT_EDGE, linewidth=0.85))
    ax.add_patch(Rectangle((0.0, 0.88), 1.0, 0.12, facecolor=HEADER_FACE, edgecolor=LIGHT_EDGE, linewidth=0.85))
    ax.text(0.50, 0.94, "Learning-guided exact branch-price-and-cut workflow", fontsize=10.6, fontweight="semibold", color=INK, ha="center", va="center")

    def group_box(x0: float, y0: float, width: float, height: float, title: str) -> None:
        ax.add_patch(Rectangle((x0, y0), width, height, facecolor="none", edgecolor="#8B969B", linewidth=0.70, linestyle=(0, (4, 3))))
        ax.text(x0 + 0.012, y0 + height - 0.018, title, fontsize=9.0, fontweight="semibold", color=MUTED, ha="left", va="top", bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.7})

    def process_box(x0: float, y0: float, width: float, height: float, text_value: str, *, face: str = "white", edge: str = "#7F8A90", fontsize: float = 9.0) -> tuple[float, float, float, float]:
        ax.add_patch(Rectangle((x0, y0), width, height, facecolor=face, edgecolor=edge, linewidth=0.75))
        ax.text(x0 + width / 2.0, y0 + height / 2.0, text_value, fontsize=fontsize, color=INK, ha="center", va="center", linespacing=1.05)
        return (x0, y0, width, height)

    def decision(cx: float, cy: float, half_w: float, half_h: float, text_value: str) -> tuple[float, float, float, float]:
        ax.add_patch(Polygon(((cx, cy + half_h), (cx + half_w, cy), (cx, cy - half_h), (cx - half_w, cy)), closed=True, facecolor="white", edgecolor="#6F7B81", linewidth=0.75))
        ax.text(cx, cy, text_value, fontsize=8.4, color=INK, ha="center", va="center", linespacing=0.95)
        return (cx, cy, half_w, half_h)

    def straight_arrow(start: tuple[float, float], end: tuple[float, float], *, color: str = "#59646A", width: float = 0.85) -> None:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8.8, linewidth=width, color=color, shrinkA=1.0, shrinkB=1.0))

    group_box(0.020, 0.455, 0.960, 0.395, "A  Column generation at the current node")
    rmp = process_box(0.050, 0.610, 0.110, 0.105, "Solve restricted\nmaster problem")
    fast = process_box(0.195, 0.610, 0.130, 0.105, "Bidirectional search\nand batch acceptance")
    exact = process_box(0.365, 0.595, 0.155, 0.135, "Complete SPPRC pricing\nDeterministic fallback", face="#F1F6F9", edge="#7A9AAD")
    ax.add_patch(Rectangle((0.382, 0.742), 0.121, 0.045, facecolor="#E4EEF5", edgecolor="#8EAFC1", linewidth=0.55))
    ax.text(0.4425, 0.7645, "GAT local ordering", fontsize=8.5, color="#315E78", ha="center", va="center")
    complete = decision(0.605, 0.662, 0.052, 0.083, "Pricing\ncomplete?")
    negative = decision(0.750, 0.662, 0.052, 0.083, "Negative\ncolumn?")
    valid_bound = process_box(0.845, 0.610, 0.115, 0.105, "Valid node\nlower bound", face="#FFF8D8", edge="#B7A45A")
    unresolved = process_box(0.545, 0.505, 0.120, 0.055, "Node unresolved", face="#FAEEEE", edge="#B77A7A", fontsize=8.6)
    batch = process_box(0.690, 0.505, 0.120, 0.055, "Verify and add batch", face="#F4F7F8", fontsize=8.5)

    straight_arrow((rmp[0] + rmp[2], 0.662), (fast[0], 0.662))
    straight_arrow((fast[0] + fast[2], 0.662), (exact[0], 0.662))
    ax.text(0.345, 0.680, "none", fontsize=8.1, color=MUTED, ha="center", va="bottom")
    straight_arrow((exact[0] + exact[2], 0.662), (complete[0] - complete[2], 0.662))
    straight_arrow((complete[0] + complete[2], 0.662), (negative[0] - negative[2], 0.662))
    ax.text(0.676, 0.680, "Yes", fontsize=8.2, color=MUTED, ha="center", va="bottom")
    straight_arrow((negative[0] + negative[2], 0.662), (valid_bound[0], 0.662))
    ax.text(0.826, 0.680, "No", fontsize=8.2, color=MUTED, ha="center", va="bottom")
    straight_arrow((complete[0], complete[1] - complete[3]), (complete[0], unresolved[1] + unresolved[3]))
    ax.text(complete[0] + 0.012, 0.575, "No", fontsize=8.2, color=MUTED, ha="left", va="center")
    straight_arrow((negative[0], negative[1] - negative[3]), (negative[0], batch[1] + batch[3]))
    ax.text(negative[0] + 0.012, 0.575, "Yes", fontsize=8.2, color=MUTED, ha="left", va="center")

    # Negative columns return to the RMP through one unobstructed feedback line.
    ax.plot([batch[0] + batch[2] / 2.0, batch[0] + batch[2] / 2.0, 0.105], [batch[1], 0.475, 0.475], color=ACCENT_RED, linewidth=0.8)
    ax.plot([(fast[0] + fast[2] / 2.0), (fast[0] + fast[2] / 2.0)], [fast[1], 0.475], color=ACCENT_RED, linewidth=0.8)
    ax.text((fast[0] + fast[2] / 2.0), 0.545, "accepted batch", fontsize=8.0, color=ACCENT_RED, ha="center", va="center", bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5})
    straight_arrow((0.105, 0.475), (0.105, rmp[1]), color=ACCENT_RED, width=0.8)
    ax.text(0.405, 0.475, "verified negative columns", fontsize=8.3, color=ACCENT_RED, ha="center", va="center", bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6})

    group_box(0.020, 0.095, 0.960, 0.315, "B  Node decision and tree control")
    root_cut = process_box(0.055, 0.220, 0.135, 0.095, "Root node:\nseparate SRI-3", face="#FFFDF2", edge="#A99A62")
    cuts = decision(0.285, 0.268, 0.050, 0.075, "Cuts\nadded?")
    disposition = (0.390, 0.165, 0.235, 0.205)
    ax.add_patch(Rectangle((disposition[0], disposition[1]), disposition[2], disposition[3], facecolor="#F8FAFA", edgecolor="#7F8A90", linewidth=0.75))
    ax.add_patch(Rectangle((disposition[0], disposition[1] + 0.155), disposition[2], 0.050, facecolor=HEADER_FACE, edgecolor="#7F8A90", linewidth=0.60))
    ax.text(disposition[0] + disposition[2] / 2.0, disposition[1] + 0.180, "Node disposition", fontsize=8.9, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text(disposition[0] + 0.018, disposition[1] + 0.118, "Integral: update incumbent", fontsize=8.2, color=INK, ha="left", va="center")
    ax.text(disposition[0] + 0.018, disposition[1] + 0.073, "Bound/infeasible: close node", fontsize=8.2, color=INK, ha="left", va="center")
    ax.text(disposition[0] + 0.018, disposition[1] + 0.028, "Fractional: Ryan–Foster children", fontsize=8.2, color=INK, ha="left", va="center")
    open_nodes = decision(0.735, 0.268, 0.055, 0.080, "Open nodes\nremain?")
    optimum = process_box(0.845, 0.220, 0.120, 0.095, "Proven optimal\nsolution", face="#ECF6EE", edge="#6E9C78", fontsize=9.0)

    # Carry a valid node bound into the lower control stage without crossing content.
    ax.plot([0.9025, 0.9025, 0.1225], [valid_bound[1], 0.425, 0.425], color="#59646A", linewidth=0.8)
    straight_arrow((0.1225, 0.425), (0.1225, root_cut[1] + root_cut[3]))
    straight_arrow((root_cut[0] + root_cut[2], 0.268), (cuts[0] - cuts[2], 0.268))
    straight_arrow((cuts[0] + cuts[2], 0.268), (disposition[0], 0.268))
    ax.text(0.345, 0.286, "No", fontsize=8.2, color=MUTED, ha="center", va="bottom")
    straight_arrow((disposition[0] + disposition[2], 0.268), (open_nodes[0] - open_nodes[2], 0.268))
    straight_arrow((open_nodes[0] + open_nodes[2], 0.268), (optimum[0], 0.268))
    ax.text(0.817, 0.286, "No", fontsize=8.2, color=MUTED, ha="center", va="bottom")

    # Root cuts and remaining open nodes re-enter the current-node processing loop.
    ax.plot([cuts[0], cuts[0], 0.035, 0.035], [cuts[1] + cuts[3], 0.440, 0.440, 0.662], color=ACCENT_RED, linewidth=0.8)
    straight_arrow((0.035, 0.662), (rmp[0], 0.662), color=ACCENT_RED, width=0.8)
    ax.text(cuts[0] + 0.012, 0.365, "Yes", fontsize=8.2, color=ACCENT_RED, ha="left", va="center")
    ax.plot([open_nodes[0], open_nodes[0], 0.035, 0.035], [open_nodes[1] - open_nodes[3], 0.070, 0.070, 0.625], color="#59646A", linewidth=0.8)
    straight_arrow((0.035, 0.625), (rmp[0], 0.625), color="#59646A", width=0.8)
    ax.text(open_nodes[0] + 0.012, 0.165, "Yes: select next node", fontsize=8.2, color=MUTED, ha="left", va="center")

    ax.text(0.50, 0.030, "Learning changes pricing order only; feasibility, cuts, bounds, pruning, and termination remain deterministic.", fontsize=8.7, color=MUTED, ha="center", va="center")


def _draw_integrated_model_algorithm_workflow(
    ax: plt.Axes,
    *,
    instance: dict,
    maps: dict[str, np.ndarray],
    terrain: np.ndarray,
) -> None:
    """Integrate lunar model construction and the exact BPC algorithm in one flow."""
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect("auto")
    ax.axis("off")

    panels = (
        (0.012, 0.152, "Mission instance"),
        (0.172, 0.332, "Candidate-path network"),
        (0.352, 0.502, "Journey-column model"),
        (0.522, 0.702, "Column generation"),
        (0.722, 0.852, "Cut, branch, and prune"),
        (0.872, 0.988, "Exact fleet plan"),
    )
    panel_y0, panel_y1, header_y0 = 0.115, 0.905, 0.825

    for stage, (x0, x1, title) in enumerate(panels, start=1):
        ax.add_patch(Rectangle((x0, panel_y0), x1 - x0, panel_y1 - panel_y0, facecolor="white", edgecolor=LIGHT_EDGE, linewidth=0.75))
        ax.add_patch(Rectangle((x0, header_y0), x1 - x0, panel_y1 - header_y0, facecolor=HEADER_FACE, edgecolor=LIGHT_EDGE, linewidth=0.75))
        badge_x = x0 + 0.013
        badge_y = (header_y0 + panel_y1) / 2.0
        ax.add_patch(Circle((badge_x, badge_y), 0.0095, facecolor="#D8E2E7", edgecolor="#87959C", linewidth=0.55))
        ax.text(badge_x, badge_y, str(stage), fontsize=7.5, fontweight="semibold", color=INK, ha="center", va="center")
        header_fontsize = 7.6 if stage in (2, 5, 6) else 8.2
        ax.text(x0 + 0.027, badge_y, title, fontsize=header_fontsize, fontweight="semibold", color=INK, ha="left", va="center")

    def process_box(x0: float, y0: float, width: float, height: float, text_value: str, *, face: str = "white", edge: str = "#7C878D", fontsize: float = 8.4) -> tuple[float, float, float, float]:
        ax.add_patch(Rectangle((x0, y0), width, height, facecolor=face, edgecolor=edge, linewidth=0.65))
        ax.text(x0 + width / 2.0, y0 + height / 2.0, text_value, fontsize=fontsize, color=INK, ha="center", va="center", linespacing=1.0)
        return (x0, y0, width, height)

    def decision(cx: float, cy: float, half_w: float, half_h: float, text_value: str) -> tuple[float, float, float, float]:
        ax.add_patch(Polygon(((cx, cy + half_h), (cx + half_w, cy), (cx, cy - half_h), (cx - half_w, cy)), closed=True, facecolor="white", edgecolor="#6F7B81", linewidth=0.65))
        ax.text(cx, cy, text_value, fontsize=7.7, color=INK, ha="center", va="center", linespacing=0.92)
        return (cx, cy, half_w, half_h)

    def flow_arrow(start: tuple[float, float], end: tuple[float, float], *, color: str = "#59646A", width: float = 0.85, curvature: float = 0.0) -> None:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8.6, linewidth=width, color=color, connectionstyle=f"arc3,rad={curvature:.3f}", shrinkA=1.0, shrinkB=1.0))

    # 1. Mission instance: real lunar background, three task classes, and a star depot.
    x0, x1, _ = panels[0]
    map_extent = (x0 + 0.008, x1 - 0.008, 0.285, 0.805)
    ax.imshow(terrain, extent=map_extent, origin="upper", aspect="auto", zorder=0)
    ax.add_patch(Rectangle((map_extent[0], map_extent[2]), map_extent[1] - map_extent[0], map_extent[3] - map_extent[2], fill=False, edgecolor="#69747A", linewidth=0.55, zorder=2))
    ax.text(map_extent[0] + 0.004, map_extent[3] - 0.018, "50 km × 50 km", fontsize=8.2, color=INK, ha="left", va="top", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.6}, zorder=5)
    task_ids = ("ice_site_001", "ice_site_003", "ice_site_004", "ice_site_006", "ice_site_007", "ice_site_009", "ice_site_018")
    for number, task_id in enumerate(task_ids, start=1):
        task = instance["tasks"][task_id]
        x_km, y_km = (float(value) for value in task["xy_km"])
        px = map_extent[0] + 0.06 * (map_extent[1] - map_extent[0]) + 0.88 * (map_extent[1] - map_extent[0]) * x_km / 50.0
        py = map_extent[2] + 0.06 * (map_extent[3] - map_extent[2]) + 0.88 * (map_extent[3] - map_extent[2]) * y_km / 50.0
        _task_marker(ax, px, py, mode=str(task["operation_mode"]), size=76.0, label=str(number), label_fontsize=6.5)
    _depot_marker(ax, (map_extent[0] + map_extent[1]) / 2.0, (map_extent[2] + map_extent[3]) / 2.0, size=155.0, label_fontsize=6.5)
    for index, (mode, label) in enumerate((("detect", "detect"), ("sample", "sample"), ("drill", "drill"))):
        px = x0 + 0.028 + 0.043 * index
        _task_marker(ax, px, 0.205, mode=mode, size=42.0)
        ax.text(px, 0.158, label, fontsize=7.2, color=MUTED, ha="center", va="center")

    # 2. Environmental layers are fused before heterogeneous local paths are generated.
    x0, x1, _ = panels[1]
    layer_specs = (("dem", "terrain", 0.730), ("illumination", "light / shadow", 0.645), ("risk", "traversal risk", 0.560))
    for key, label, y0 in layer_specs:
        ax.imshow(maps[key], extent=(x0 + 0.012, x1 - 0.012, y0, y0 + 0.065), origin="upper", aspect="auto", zorder=1)
        ax.text(x0 + 0.016, y0 + 0.047, label, fontsize=7.5, color=INK, ha="left", va="center", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 0.4}, zorder=3)
    flow_arrow(((x0 + x1) / 2.0, 0.548), ((x0 + x1) / 2.0, 0.510), color="#7B878D", width=0.65)
    path_extent = (x0 + 0.012, x1 - 0.012, 0.275, 0.505)
    ax.imshow(terrain, extent=path_extent, origin="upper", aspect="auto", alpha=0.32, zorder=0)
    source = (x0 + 0.030, 0.325)
    target = (x1 - 0.030, 0.455)
    _task_marker(ax, *source, mode="detect", size=58.0, label="i", label_fontsize=6.4)
    _task_marker(ax, *target, mode="sample", size=64.0, label="j", label_fontsize=6.4)
    for key, curvature in (("time", -0.26), ("energy", 0.0), ("risk", 0.26)):
        flow_arrow(source, target, color=PATH_COLORS[key], width=1.15, curvature=curvature)
    ax.text((x0 + x1) / 2.0, 0.220, "time · energy · shadow · risk", fontsize=7.6, color=INK, ha="center", va="center")
    ax.text((x0 + x1) / 2.0, 0.160, "retain multiple paths per directed leg", fontsize=7.2, color=MUTED, ha="center", va="center")

    # 3. A journey column contains all ordered depot-to-depot trips of one rover.
    x0, x1, _ = panels[2]
    color = VEHICLE_COLORS["V1"]
    depot = ((x0 + x1) / 2.0, 0.585)
    trip_1 = ((x0 + 0.025, 0.695), (x0 + 0.065, 0.755))
    trip_2 = ((x1 - 0.025, 0.700), (x1 - 0.040, 0.485))
    for start, end in ((depot, trip_1[0]), (trip_1[0], trip_1[1]), (trip_1[1], depot), (depot, trip_2[0]), (trip_2[0], trip_2[1]), (trip_2[1], depot)):
        flow_arrow(start, end, color=color, width=1.15)
    _depot_marker(ax, *depot, size=140.0, label_fontsize=6.4)
    for point, mode in ((trip_1[0], "detect"), (trip_1[1], "sample"), (trip_2[0], "drill"), (trip_2[1], "sample")):
        _task_marker(ax, *point, mode=mode, size=58.0)
    ax.text(x0 + 0.026, 0.785, "trip 1", fontsize=7.5, color=color, fontweight="semibold", ha="left", va="center")
    ax.text(x1 - 0.055, 0.785, "trip 2", fontsize=7.5, color=color, fontweight="semibold", ha="left", va="center")
    ax.text((x0 + x1) / 2.0, 0.420, "return · recharge · relaunch", fontsize=7.5, color=INK, ha="center", va="center")
    for offset in range(3):
        bx = x0 + 0.032 + 0.010 * offset
        by = 0.225 + 0.020 * offset
        ax.add_patch(Rectangle((bx, by), 0.073, 0.085, facecolor="white", edgecolor=LIGHT_EDGE, linewidth=0.55))
        ax.plot([bx + 0.010, bx + 0.060], [by + 0.045, by + 0.045], color=VEHICLE_COLORS[("V1", "V2", "V3")[offset]], linewidth=1.5)
        ax.scatter([bx + 0.022, bx + 0.050], [by + 0.045, by + 0.045], s=16, facecolor=TASK_FACE, edgecolor=INK, linewidth=0.35, zorder=3)
    ax.text((x0 + x1) / 2.0, 0.335, "candidate journey columns", fontsize=7.3, color=MUTED, ha="center", va="center")
    ax.text((x0 + x1) / 2.0, 0.165, "service begins on arrival\ntrip departure is adjusted at the depot", fontsize=6.8, color=MUTED, ha="center", va="center", linespacing=1.05)

    # 4. Restricted master and the two-stage pricing loop.
    x0, x1, _ = panels[3]
    rmp = process_box(x0 + 0.015, 0.545, 0.065, 0.110, "Restricted\nmaster")
    fast = process_box(x0 + 0.103, 0.700, 0.064, 0.075, "Fast search\n+ batch", fontsize=7.8)
    exact = process_box(x0 + 0.098, 0.515, 0.072, 0.100, "Complete SPPRC\npricing", face="#F1F6F9", edge="#7A9AAD", fontsize=7.7)
    ax.add_patch(Rectangle((x0 + 0.105, 0.630), 0.058, 0.040, facecolor="#E4EEF5", edgecolor="#8EAFC1", linewidth=0.50))
    ax.text(x0 + 0.134, 0.650, "GAT order", fontsize=7.1, color="#315E78", ha="center", va="center")
    negative = decision(x0 + 0.134, 0.430, 0.035, 0.050, "Negative\ncolumn?")
    complete = decision(x0 + 0.055, 0.365, 0.033, 0.048, "Pricing\ncomplete?")
    bound = process_box(x0 + 0.015, 0.225, 0.075, 0.075, "Valid node\nlower bound", face="#FFF8D8", edge="#B7A45A", fontsize=7.6)
    unresolved = process_box(x0 + 0.105, 0.225, 0.064, 0.075, "Unresolved\nnode", face="#FAEEEE", edge="#B77A7A", fontsize=7.5)
    flow_arrow((rmp[0] + rmp[2], 0.600), (fast[0], 0.735))
    flow_arrow((fast[0] + fast[2] / 2.0, fast[1]), (exact[0] + exact[2] / 2.0, exact[1] + exact[3]))
    ax.text(x0 + 0.142, 0.680, "none", fontsize=6.8, color=MUTED, ha="center", va="center")
    flow_arrow((exact[0] + exact[2] / 2.0, exact[1]), (negative[0], negative[1] + negative[3]))
    flow_arrow((negative[0] - negative[2], negative[1]), (complete[0] + complete[2], complete[1]))
    ax.text(x0 + 0.094, 0.414, "No", fontsize=6.8, color=MUTED, ha="center", va="center")
    flow_arrow((complete[0], complete[1] - complete[3]), (bound[0] + bound[2] / 2.0, bound[1] + bound[3]))
    ax.text(x0 + 0.045, 0.312, "Yes", fontsize=6.8, color=MUTED, ha="center", va="center")
    flow_arrow((complete[0] + complete[2], complete[1]), (unresolved[0], unresolved[1] + unresolved[3] / 2.0))
    ax.text(x0 + 0.096, 0.355, "No", fontsize=6.8, color=MUTED, ha="center", va="center")
    # Accepted fast batches and exact negative columns both return to the RMP.
    ax.plot([fast[0] + fast[2], x1 - 0.004, x1 - 0.004, rmp[0] + rmp[2] / 2.0], [0.735, 0.735, 0.690, 0.690], color=ACCENT_RED, linewidth=0.75)
    flow_arrow((rmp[0] + rmp[2] / 2.0, 0.690), (rmp[0] + rmp[2] / 2.0, rmp[1] + rmp[3]), color=ACCENT_RED, width=0.75)
    ax.text(x1 - 0.008, 0.750, "batch", fontsize=6.8, color=ACCENT_RED, ha="right", va="bottom")
    ax.plot([negative[0] + negative[2], x1 - 0.010, x1 - 0.010, rmp[0] + rmp[2] / 2.0], [negative[1], 0.430, 0.500, 0.500], color=ACCENT_RED, linewidth=0.75)
    flow_arrow((rmp[0] + rmp[2] / 2.0, 0.500), (rmp[0] + rmp[2] / 2.0, rmp[1]), color=ACCENT_RED, width=0.75)
    ax.text(x1 - 0.012, 0.448, "Yes", fontsize=6.8, color=ACCENT_RED, ha="right", va="bottom")
    ax.text((x0 + x1) / 2.0, 0.155, "learning changes label order only", fontsize=7.1, color=MUTED, ha="center", va="center")

    # 5. Root strengthening, deterministic node disposition, and Ryan-Foster branching.
    x0, x1, _ = panels[4]
    root_cut = process_box(x0 + 0.012, 0.185, 0.106, 0.085, "Root valid inequalities\n(SRI-3)", face="#FFFDF2", edge="#A99A62", fontsize=7.2)
    cuts = decision((x0 + x1) / 2.0, 0.345, 0.038, 0.050, "Cuts\nadded?")
    status_x, status_y, status_w, status_h = x0 + 0.012, 0.445, 0.106, 0.145
    ax.add_patch(Rectangle((status_x, status_y), status_w, status_h, facecolor="#F8FAFA", edgecolor="#7F8A90", linewidth=0.65))
    ax.add_patch(Rectangle((status_x, status_y + 0.105), status_w, 0.040, facecolor=HEADER_FACE, edgecolor="#7F8A90", linewidth=0.55))
    ax.text(status_x + status_w / 2.0, status_y + 0.125, "Node status", fontsize=7.8, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text(status_x + 0.008, status_y + 0.083, "integral → incumbent", fontsize=7.2, color=INK, ha="left", va="center")
    ax.text(status_x + 0.008, status_y + 0.050, "bound/infeasible → close", fontsize=7.0, color=INK, ha="left", va="center")
    ax.text(status_x + 0.008, status_y + 0.017, "fractional → branch", fontsize=7.2, color=INK, ha="left", va="center")
    root = ((x0 + x1) / 2.0, 0.740)
    children = ((x0 + 0.035, 0.660), (x1 - 0.035, 0.660))
    for child in children:
        ax.plot([root[0], child[0]], [root[1], child[1]], color="#59646A", linewidth=0.75)
    ax.scatter([root[0]], [root[1]], s=24, facecolor="white", edgecolor=INK, linewidth=0.60)
    for child, label in zip(children, ("same", "separate")):
        ax.scatter([child[0]], [child[1]], s=22, facecolor="white", edgecolor=VEHICLE_COLORS["V1"], linewidth=0.65)
        ax.text(child[0], 0.625, label, fontsize=6.8, color=MUTED, ha="center", va="center")
    ax.text(root[0], 0.785, "Ryan–Foster", fontsize=7.5, color=INK, ha="center", va="center")
    flow_arrow((root_cut[0] + root_cut[2] / 2.0, root_cut[1] + root_cut[3]), (cuts[0], cuts[1] - cuts[3]))
    flow_arrow((cuts[0], cuts[1] + cuts[3]), (status_x + status_w / 2.0, status_y))
    ax.text(cuts[0] + 0.010, 0.405, "No", fontsize=6.8, color=MUTED, ha="left", va="center")
    flow_arrow((status_x + status_w / 2.0, status_y + status_h), (root[0], root[1] - 0.015))
    # New root cuts return to the master problem.
    ax.plot([cuts[0] - cuts[2], x0 + 0.004, x0 + 0.004, panels[3][0] + 0.050], [cuts[1], cuts[1], 0.095, 0.095], color=ACCENT_RED, linewidth=0.75)
    flow_arrow((panels[3][0] + 0.050, 0.095), (panels[3][0] + 0.050, rmp[1]), color=ACCENT_RED, width=0.75)
    ax.text(x0 + 0.014, 0.325, "Yes", fontsize=6.8, color=ACCENT_RED, ha="left", va="center")

    # 6. Tree closure yields a proof-qualified fleet plan.
    x0, x1, _ = panels[5]
    open_nodes = decision((x0 + x1) / 2.0, 0.710, 0.045, 0.058, "Open nodes\nremain?")
    optimum = process_box(x0 + 0.016, 0.565, 0.084, 0.075, "Proven optimal", face="#ECF6EE", edge="#6E9C78", fontsize=7.8)
    flow_arrow((open_nodes[0], open_nodes[1] - open_nodes[3]), (optimum[0] + optimum[2] / 2.0, optimum[1] + optimum[3]))
    ax.text(open_nodes[0] + 0.010, 0.655, "No", fontsize=6.8, color=MUTED, ha="left", va="center")
    task_modes = {"1": "drill", "2": "detect", "3": "sample", "4": "detect", "5": "drill", "6": "sample", "7": "sample"}
    rows = ((0.485, "V1", VEHICLE_COLORS["V1"], ("1", "3", "6")), (0.405, "V2", VEHICLE_COLORS["V2"], ("2", "5")), (0.325, "V3", VEHICLE_COLORS["V3"], ("4", "7")))
    for y, vehicle, vehicle_color, task_numbers in rows:
        ax.text(x0 + 0.009, y, vehicle, fontsize=7.2, fontweight="semibold", color=vehicle_color, ha="left", va="center")
        route_x = np.linspace(x0 + 0.036, x1 - 0.010, len(task_numbers) + 2)
        ax.plot(route_x, np.full_like(route_x, y), color=vehicle_color, linewidth=1.20, zorder=1)
        _depot_marker(ax, route_x[0], y, size=43.0, label_fontsize=4.7)
        _depot_marker(ax, route_x[-1], y, size=43.0, label_fontsize=4.7)
        for px, task_number in zip(route_x[1:-1], task_numbers):
            ax.scatter([px], [y], s=42, marker=TASK_MARKERS[task_modes[task_number]], facecolor=TASK_FACE, edgecolor=INK, linewidth=0.50)
            ax.text(px, y, task_number, fontsize=5.4, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text((x0 + x1) / 2.0, 0.260, "normalized objective", fontsize=7.2, fontweight="semibold", color=INK, ha="center", va="center")
    objective_rows = ((0.220, "operating cost", "#EAF1F7", "#7B9DB8"), (0.180, "risk", "#F9EAEA", "#B97C7C"), (0.140, "0.4 × weighted completion", "#FFF5D9", "#B89E55"))
    for y, label, face_color, edge_color in objective_rows:
        ax.add_patch(Rectangle((x0 + 0.012, y - 0.015), x1 - x0 - 0.024, 0.030, facecolor=face_color, edgecolor=edge_color, linewidth=0.55))
        ax.text((x0 + x1) / 2.0, y, label, fontsize=6.4, color=INK, ha="center", va="center")
    # Child nodes and other remaining open nodes return to the RMP.
    ax.plot([open_nodes[0] - open_nodes[2], x0 - 0.006, x0 - 0.006, panels[3][0] + 0.028], [open_nodes[1], open_nodes[1], 0.055, 0.055], color="#59646A", linewidth=0.75)
    flow_arrow((panels[3][0] + 0.028, 0.055), (panels[3][0] + 0.028, rmp[1]), color="#59646A", width=0.75)
    ax.text(x0 - 0.010, open_nodes[1] + 0.020, "Yes", fontsize=6.8, color=MUTED, ha="right", va="bottom")

    # Main model-to-algorithm flow arrows between adjacent stages.
    for left, right, y in ((panels[0], panels[1], 0.540), (panels[1], panels[2], 0.540), (panels[2], panels[3], 0.600)):
        flow_arrow((left[1] + 0.003, y), (right[0] - 0.003, y), color=INK, width=1.0)
    flow_arrow((panels[3][1] + 0.003, 0.263), (root_cut[0] - 0.003, 0.263), color=INK, width=1.0)
    flow_arrow((panels[4][1] + 0.003, 0.710), (open_nodes[0] - open_nodes[2] - 0.003, 0.710), color=INK, width=1.0)


def _draw_trc_model_algorithm_flowchart(
    ax: plt.Axes,
    *,
    instance: dict,
    maps: dict[str, np.ndarray],
    terrain: np.ndarray,
) -> None:
    """Draw one continuous model-and-algorithm flowchart without stage panels."""
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect("auto")
    ax.axis("off")

    def process_box(
        x0: float,
        y0: float,
        width: float,
        height: float,
        text_value: str,
        *,
        face: str = "#F8FAFA",
        edge: str = "#748087",
        fontsize: float = 8.0,
        radius: float = 0.004,
        linewidth: float = 0.70,
    ) -> tuple[float, float, float, float]:
        patch = FancyBboxPatch(
            (x0, y0),
            width,
            height,
            boxstyle=f"round,pad=0.004,rounding_size={radius}",
            facecolor=face,
            edgecolor=edge,
            linewidth=linewidth,
        )
        ax.add_patch(patch)
        ax.text(
            x0 + width / 2.0,
            y0 + height / 2.0,
            text_value,
            fontsize=fontsize,
            color=INK,
            ha="center",
            va="center",
            linespacing=1.02,
        )
        return (x0, y0, width, height)

    def decision(
        cx: float,
        cy: float,
        half_w: float,
        half_h: float,
        text_value: str,
        *,
        fontsize: float = 7.4,
    ) -> tuple[float, float, float, float]:
        ax.add_patch(
            Polygon(
                ((cx, cy + half_h), (cx + half_w, cy), (cx, cy - half_h), (cx - half_w, cy)),
                closed=True,
                facecolor="white",
                edgecolor="#6E7A80",
                linewidth=0.72,
            )
        )
        ax.text(cx, cy, text_value, fontsize=fontsize, color=INK, ha="center", va="center", linespacing=0.94)
        return (cx, cy, half_w, half_h)

    def arrow(
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        color: str = "#536168",
        width: float = 0.85,
        curvature: float = 0.0,
        zorder: int = 12,
    ) -> None:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=8.2,
                linewidth=width,
                color=color,
                connectionstyle=f"arc3,rad={curvature:.3f}",
                shrinkA=1.5,
                shrinkB=1.5,
                zorder=zorder,
            )
        )

    def feedback(
        points: tuple[tuple[float, float], ...],
        *,
        color: str,
        width: float = 0.78,
    ) -> None:
        for start, end in zip(points[:-2], points[1:-1]):
            ax.plot((start[0], end[0]), (start[1], end[1]), color=color, linewidth=width, zorder=7)
        arrow(points[-2], points[-1], color=color, width=width, zorder=8)

    # Mission information enters the solution process as one input object.
    scene_x, scene_y, scene_w, scene_h = 0.018, 0.170, 0.152, 0.700
    ax.add_patch(
        FancyBboxPatch(
            (scene_x, scene_y),
            scene_w,
            scene_h,
            boxstyle="round,pad=0.004,rounding_size=0.006",
            facecolor="white",
            edgecolor="#7B878D",
            linewidth=0.78,
        )
    )
    ax.text(scene_x + scene_w / 2.0, 0.838, "Lunar mission instance", fontsize=8.8, fontweight="semibold", color=INK, ha="center", va="center")
    map_extent = (scene_x + 0.012, scene_x + scene_w - 0.012, 0.458, 0.810)
    ax.imshow(terrain, extent=map_extent, origin="upper", aspect="auto", zorder=0)
    ax.add_patch(Rectangle((map_extent[0], map_extent[2]), map_extent[1] - map_extent[0], map_extent[3] - map_extent[2], fill=False, edgecolor="#6F7B81", linewidth=0.55, zorder=2))
    ax.text(map_extent[0] + 0.004, map_extent[3] - 0.014, "50 km × 50 km", fontsize=6.8, color=INK, ha="left", va="top", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.45}, zorder=5)
    task_ids = ("ice_site_001", "ice_site_003", "ice_site_004", "ice_site_006", "ice_site_007", "ice_site_009", "ice_site_018")
    for number, task_id in enumerate(task_ids, start=1):
        task = instance["tasks"][task_id]
        x_km, y_km = (float(value) for value in task["xy_km"])
        px = map_extent[0] + 0.06 * (map_extent[1] - map_extent[0]) + 0.88 * (map_extent[1] - map_extent[0]) * x_km / 50.0
        py = map_extent[2] + 0.06 * (map_extent[3] - map_extent[2]) + 0.88 * (map_extent[3] - map_extent[2]) * y_km / 50.0
        _task_marker(ax, px, py, mode=str(task["operation_mode"]), size=55.0, label=str(number), label_fontsize=5.2)
    _depot_marker(ax, (map_extent[0] + map_extent[1]) / 2.0, (map_extent[2] + map_extent[3]) / 2.0, size=112.0, label_fontsize=5.3)
    layer_specs = (("dem", "terrain"), ("illumination", "illumination"), ("risk", "risk"))
    for index, (key, label) in enumerate(layer_specs):
        y0 = 0.382 - 0.060 * index
        ax.imshow(maps[key], extent=(scene_x + 0.014, scene_x + scene_w - 0.014, y0, y0 + 0.045), origin="upper", aspect="auto", zorder=1)
        ax.text(scene_x + 0.018, y0 + 0.031, label, fontsize=6.1, color=INK, ha="left", va="center", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 0.30}, zorder=3)
    legend_items = (("detect", "detect"), ("sample", "sample"), ("drill", "drill"))
    for index, (mode, label) in enumerate(legend_items):
        px = scene_x + 0.028 + 0.036 * index
        _task_marker(ax, px, 0.220, mode=mode, size=35.0)
        ax.text(px, 0.188, label, fontsize=5.7, color=MUTED, ha="center", va="center")
    _depot_marker(ax, scene_x + 0.136, 0.220, size=62.0, label=None)
    ax.text(scene_x + 0.136, 0.188, "depot", fontsize=5.7, color=MUTED, ha="center", va="center")

    # Network and route-column construction is the model input to the BPC loop.
    model_x, model_y, model_w, model_h = 0.195, 0.170, 0.170, 0.700
    ax.add_patch(
        FancyBboxPatch(
            (model_x, model_y),
            model_w,
            model_h,
            boxstyle="round,pad=0.004,rounding_size=0.006",
            facecolor="white",
            edgecolor="#7B878D",
            linewidth=0.78,
        )
    )
    ax.text(model_x + model_w / 2.0, 0.838, "Multi-path, multi-trip model", fontsize=8.6, fontweight="semibold", color=INK, ha="center", va="center")
    path_extent = (model_x + 0.014, model_x + model_w - 0.014, 0.622, 0.804)
    ax.imshow(terrain, extent=path_extent, origin="upper", aspect="auto", alpha=0.38, zorder=0)
    source = (model_x + 0.032, 0.660)
    target = (model_x + model_w - 0.030, 0.762)
    for key, curvature in (("time", -0.28), ("energy", 0.0), ("risk", 0.28)):
        arrow(source, target, color=PATH_COLORS[key], width=1.10, curvature=curvature, zorder=3)
    _task_marker(ax, *source, mode="detect", size=52.0, label="i", label_fontsize=5.3)
    _task_marker(ax, *target, mode="sample", size=56.0, label="j", label_fontsize=5.3)
    ax.text(model_x + model_w / 2.0, 0.596, "alternative directed paths", fontsize=6.9, color=INK, ha="center", va="center")
    ax.text(model_x + model_w / 2.0, 0.566, "time · energy · shadow · risk", fontsize=6.4, color=MUTED, ha="center", va="center")

    depot = (model_x + model_w / 2.0, 0.430)
    route_nodes = (
        (model_x + 0.035, 0.490, "detect"),
        (model_x + 0.060, 0.525, "sample"),
        (model_x + model_w - 0.038, 0.495, "drill"),
        (model_x + model_w - 0.052, 0.365, "sample"),
    )
    teal = VEHICLE_COLORS["V1"]
    route_points = ((depot, route_nodes[0][:2]), (route_nodes[0][:2], route_nodes[1][:2]), (route_nodes[1][:2], depot), (depot, route_nodes[2][:2]), (route_nodes[2][:2], route_nodes[3][:2]), (route_nodes[3][:2], depot))
    for start, end in route_points:
        arrow(start, end, color=teal, width=1.05, zorder=3)
    _depot_marker(ax, *depot, size=98.0, label_fontsize=5.0)
    for px, py, mode in route_nodes:
        _task_marker(ax, px, py, mode=mode, size=46.0)
    ax.text(model_x + model_w / 2.0, 0.328, "depot-to-depot trips form a journey column", fontsize=6.5, color=INK, ha="center", va="center")
    ax.text(model_x + model_w / 2.0, 0.276, "time windows · capacity · energy · shadow", fontsize=6.1, color=MUTED, ha="center", va="center")
    ax.text(model_x + model_w / 2.0, 0.224, "service starts on arrival\ndeparture is adjusted at the depot", fontsize=5.9, color=MUTED, ha="center", va="center", linespacing=1.05)
    ax.text(model_x + model_w / 2.0, 0.190, "normalized objective:\noperating cost + risk + 0.4 × weighted completion", fontsize=5.7, color=INK, ha="center", va="center", linespacing=1.02)

    arrow((scene_x + scene_w + 0.004, 0.525), (model_x - 0.004, 0.525), color=INK, width=1.00)

    initial = process_box(0.405, 0.805, 0.125, 0.074, "Initialize the BPC tree\nand feasible journey pool", fontsize=7.4)
    rmp = process_box(0.405, 0.675, 0.125, 0.074, "Select an open node and\nsolve the restricted master", fontsize=7.3)
    fast = process_box(0.405, 0.545, 0.125, 0.074, "Bidirectional fast pricing", fontsize=7.4)
    fast_found = decision(0.4675, 0.425, 0.050, 0.047, "Negative columns\nfound?", fontsize=6.8)
    batch = process_box(0.565, 0.389, 0.110, 0.072, "Accept a column batch", face="#FAF0F0", edge="#B97C7C", fontsize=7.1)

    arrow((model_x + model_w + 0.004, 0.842), (initial[0] - 0.004, 0.842), color=INK, width=1.00)
    arrow((initial[0] + initial[2] / 2.0, initial[1]), (rmp[0] + rmp[2] / 2.0, rmp[1] + rmp[3]), color=INK, width=0.92)
    arrow((rmp[0] + rmp[2] / 2.0, rmp[1]), (fast[0] + fast[2] / 2.0, fast[1] + fast[3]), color=INK, width=0.92)
    arrow((fast[0] + fast[2] / 2.0, fast[1]), (fast_found[0], fast_found[1] + fast_found[3]), color=INK, width=0.92)
    arrow((fast_found[0] + fast_found[2], fast_found[1]), (batch[0], batch[1] + batch[3] / 2.0), color=ACCENT_RED, width=0.82)
    ax.text(0.535, 0.442, "Yes", fontsize=6.4, color=ACCENT_RED, ha="center", va="bottom")

    exact_x, exact_y, exact_w, exact_h = 0.405, 0.285, 0.125, 0.088
    ax.add_patch(FancyBboxPatch((exact_x, exact_y), exact_w, exact_h, boxstyle="round,pad=0.004,rounding_size=0.004", facecolor="#F0F6F9", edgecolor="#7595A7", linewidth=0.75))
    ax.text(exact_x + exact_w / 2.0, exact_y + 0.061, "Complete SPPRC pricing", fontsize=7.4, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text(exact_x + exact_w / 2.0, exact_y + 0.035, "GAT label order", fontsize=6.6, color="#315E78", ha="center", va="center")
    ax.text(exact_x + exact_w / 2.0, exact_y + 0.013, "deterministic fallback", fontsize=6.1, color=MUTED, ha="center", va="center")
    negative = decision(0.4675, 0.205, 0.050, 0.044, "Negative\ncolumn?", fontsize=7.0)
    add_exact = process_box(0.565, 0.170, 0.110, 0.070, "Add exact negative\ncolumns", face="#FAF0F0", edge="#B97C7C", fontsize=6.9)
    complete = decision(0.4675, 0.105, 0.050, 0.043, "Pricing\ncomplete?", fontsize=7.0)
    unresolved = process_box(0.365, 0.072, 0.070, 0.064, "Unresolved\nnode", face="#FAEEEE", edge="#B77A7A", fontsize=6.5)
    bound = process_box(0.565, 0.072, 0.105, 0.064, "Valid node\nlower bound", face="#FFF8D8", edge="#B7A45A", fontsize=6.9)

    arrow((fast_found[0], fast_found[1] - fast_found[3]), (exact_x + exact_w / 2.0, exact_y + exact_h), color="#536168", width=0.84)
    ax.text(0.478, 0.391, "No", fontsize=6.4, color=MUTED, ha="left", va="center")
    arrow((exact_x + exact_w / 2.0, exact_y), (negative[0], negative[1] + negative[3]), color="#536168", width=0.84)
    arrow((negative[0] + negative[2], negative[1]), (add_exact[0], add_exact[1] + add_exact[3] / 2.0), color=ACCENT_RED, width=0.82)
    ax.text(0.535, 0.222, "Yes", fontsize=6.4, color=ACCENT_RED, ha="center", va="bottom")
    arrow((negative[0], negative[1] - negative[3]), (complete[0], complete[1] + complete[3]), color="#536168", width=0.84)
    ax.text(0.478, 0.157, "No", fontsize=6.4, color=MUTED, ha="left", va="center")
    arrow((complete[0] - complete[2], complete[1]), (unresolved[0] + unresolved[2], unresolved[1] + unresolved[3] / 2.0), color="#536168", width=0.82)
    ax.text(0.443, 0.125, "No", fontsize=6.3, color=MUTED, ha="center", va="bottom")
    arrow((complete[0] + complete[2], complete[1]), (bound[0], bound[1] + bound[3] / 2.0), color="#536168", width=0.82)
    ax.text(0.535, 0.125, "Yes", fontsize=6.3, color=MUTED, ha="center", va="bottom")
    ax.text(unresolved[0] + unresolved[2] / 2.0, 0.050, "fail closed", fontsize=5.9, color="#9C5D5D", ha="center", va="center")

    # All new columns and root cuts share one unobstructed return channel to the RMP.
    feedback_rail_x = 0.695
    ax.plot((feedback_rail_x, feedback_rail_x), (0.205, 0.695), color=ACCENT_RED, linewidth=0.78, zorder=7)
    arrow((batch[0] + batch[2], batch[1] + batch[3] / 2.0), (feedback_rail_x, batch[1] + batch[3] / 2.0), color=ACCENT_RED, width=0.78)
    arrow((add_exact[0] + add_exact[2], add_exact[1] + add_exact[3] / 2.0), (feedback_rail_x, add_exact[1] + add_exact[3] / 2.0), color=ACCENT_RED, width=0.78)
    arrow((feedback_rail_x, 0.695), (rmp[0] + rmp[2], 0.695), color=ACCENT_RED, width=0.78)
    ax.text(feedback_rail_x + 0.008, 0.465, "return to RMP", fontsize=6.1, color=ACCENT_RED, rotation=90, ha="left", va="center")

    # The right-hand leg closes the exact BPC tree from bottom to top.
    root = decision(0.820, 0.105, 0.040, 0.043, "Root\nnode?", fontsize=6.8)
    sri = process_box(0.765, 0.190, 0.110, 0.064, "Separate SRI-3\nvalid inequalities", face="#FFFDF2", edge="#A99A62", fontsize=6.5)
    cuts = decision(0.820, 0.325, 0.042, 0.045, "Cuts\nadded?", fontsize=6.8)
    status_x, status_y, status_w, status_h = 0.745, 0.420, 0.150, 0.128
    ax.add_patch(FancyBboxPatch((status_x, status_y), status_w, status_h, boxstyle="round,pad=0.004,rounding_size=0.004", facecolor="#F8FAFA", edgecolor="#748087", linewidth=0.72))
    ax.text(status_x + status_w / 2.0, status_y + status_h - 0.022, "Node disposition", fontsize=7.2, fontweight="semibold", color=INK, ha="center", va="center")
    ax.text(status_x + 0.010, status_y + 0.076, "integral → update incumbent", fontsize=6.4, color=INK, ha="left", va="center")
    ax.text(status_x + 0.010, status_y + 0.046, "bound/infeasible → prune", fontsize=6.4, color=INK, ha="left", va="center")
    ax.text(status_x + 0.010, status_y + 0.017, "fractional → Ryan–Foster branch", fontsize=6.2, color=INK, ha="left", va="center")
    open_nodes = decision(0.820, 0.650, 0.052, 0.050, "Open nodes\nremain?", fontsize=6.9)
    optimum = process_box(0.755, 0.770, 0.130, 0.074, "Proven-optimal fleet plan", face="#ECF6EE", edge="#6E9C78", fontsize=7.0)

    arrow((bound[0] + bound[2], bound[1] + bound[3] / 2.0), (root[0] - root[2], root[1]), color="#536168", width=0.84)
    arrow((root[0], root[1] + root[3]), (sri[0] + sri[2] / 2.0, sri[1]), color="#536168", width=0.84)
    ax.text(root[0] + 0.011, 0.157, "Yes", fontsize=6.2, color=MUTED, ha="left", va="center")
    arrow((sri[0] + sri[2] / 2.0, sri[1] + sri[3]), (cuts[0], cuts[1] - cuts[3]), color="#536168", width=0.84)
    arrow((cuts[0], cuts[1] + cuts[3]), (status_x + status_w / 2.0, status_y), color="#536168", width=0.84)
    ax.text(cuts[0] + 0.012, 0.386, "No", fontsize=6.2, color=MUTED, ha="left", va="center")
    # Root cuts join the same RMP return rail.
    arrow((cuts[0] - cuts[2], cuts[1]), (feedback_rail_x, cuts[1]), color=ACCENT_RED, width=0.78)
    ax.text(0.716, 0.343, "Yes", fontsize=6.2, color=ACCENT_RED, ha="center", va="bottom")
    # Non-root nodes bypass the root-only cut routine.
    feedback(((root[0] + root[2], root[1]), (0.920, root[1]), (0.920, status_y + status_h / 2.0), (status_x + status_w, status_y + status_h / 2.0)), color="#536168", width=0.70)
    ax.text(0.885, 0.120, "No", fontsize=6.2, color=MUTED, ha="center", va="bottom")
    arrow((status_x + status_w / 2.0, status_y + status_h), (open_nodes[0], open_nodes[1] - open_nodes[3]), color="#536168", width=0.84)
    arrow((open_nodes[0], open_nodes[1] + open_nodes[3]), (optimum[0] + optimum[2] / 2.0, optimum[1]), color="#536168", width=0.84)
    ax.text(open_nodes[0] + 0.012, 0.716, "No", fontsize=6.2, color=MUTED, ha="left", va="center")
    # Remaining nodes return along the outer edge and re-enter node selection.
    feedback(((open_nodes[0] + open_nodes[2], open_nodes[1]), (0.925, open_nodes[1]), (0.925, 0.920), (0.545, 0.920), (0.545, 0.730), (rmp[0] + rmp[2], 0.730)), color="#536168", width=0.72)
    ax.text(0.910, 0.671, "Yes: next node", fontsize=6.1, color=MUTED, ha="right", va="bottom")

    ax.text(0.690, 0.025, "Learning changes label order in exact pricing only; feasibility, cuts, bounds, pruning, and termination remain deterministic.", fontsize=6.8, color=MUTED, ha="center", va="center")


def _figure_arrow(
    figure: plt.Figure,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    linewidth: float,
    mutation_scale: float,
    zorder: int = 30,
) -> None:
    figure.add_artist(
        FancyArrowPatch(
            start,
            end,
            transform=figure.transFigure,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=linewidth,
            color=color,
            connectionstyle="arc3,rad=0",
            zorder=zorder,
        )
    )


def main() -> int:
    if not ENVIRONMENT_PANEL_PATH.is_file():
        raise FileNotFoundError(ENVIRONMENT_PANEL_PATH)
    instance = read_json(INSTANCE_PATH)
    maps = _load_environment_thumbnails()
    terrain = _load_light_terrain_thumbnail()

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
    figure = plt.figure(figsize=(13.2, 6.2), facecolor="white")
    integrated_axis = figure.add_axes((0.008, 0.015, 0.984, 0.970))
    _draw_trc_model_algorithm_flowchart(
        integrated_axis,
        instance=instance,
        maps=maps,
        terrain=terrain,
    )

    metadata = {
        "Title": "Integrated model and exact solution workflow for lunar water-ice exploration routing",
        "Subject": "Lunar mission instance, candidate-path model, journey columns, and exact branch-price-and-cut workflow",
        "Keywords": "lunar routing, multi-path, multi-trip, exact pricing, branch-price-and-cut, learning-guided ordering",
    }
    figure.savefig(
        OUTPUT_PNG_PATH,
        dpi=OUTPUT_DPI,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata={"Software": "Matplotlib"},
    )
    figure.savefig(
        OUTPUT_PDF_PATH,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata=metadata,
    )
    plt.close(figure)

    print(f"wrote {OUTPUT_PNG_PATH}")
    print(f"wrote {OUTPUT_PDF_PATH}")
    print("layout=continuous_trc_style_model_algorithm_flowchart")
    print("model_scope=mission_instance,candidate_path_network,journey_columns,column_generation,cut_branch_prune,exact_fleet_plan")
    print("objective=normalized_operating_cost+normalized_risk+0.4*normalized_weighted_completion")
    print("waiting=depot_only; task_site_and_en_route_waiting_prohibited")
    print("algorithm_content=exact_bpc_workflow_with_learning_guided_pricing_order")
    print("selection_semantics=conceptual; not solver output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Matplotlib figures for lunar-ice real-map logical graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from lunar_ice_bpc.io.instance_io import read_json


MODE_COLOR = {"detect": "#2b83ba", "sample": "#abdda4", "drill": "#d7191c"}
PATH_STYLE = {
    "low_time": {"color": "#32b8ff", "lw": 0.85, "alpha": 0.32},
    "low_energy": {"color": "#7bd34a", "lw": 0.76, "alpha": 0.30},
    "low_risk": {"color": "#ffb84c", "lw": 0.70, "alpha": 0.30},
}

BASEMAP_LAYER_STYLE = {
    "elevation_m": {
        "title": "DEM elevation",
        "cmap": "terrain",
        "colorbar": "elevation (m)",
        "limits": None,
    },
    "risk_index": {
        "title": "Deterministic traversal risk",
        "cmap": "magma",
        "colorbar": "risk index",
        "limits": (0.0, 1.0),
    },
    "resource_index": {
        "title": "Water-ice resource potential",
        "cmap": "cividis_r",
        "colorbar": "resource index",
        "limits": (0.0, 1.0),
    },
    "illumination_index": {
        "title": "Average solar visibility",
        "cmap": "gray",
        "colorbar": "illumination index",
        "limits": (0.0, 1.0),
    },
}


def configure_scientific_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def draw_real_map_basemaps(
    preview_path: str | Path,
    output_dir: str | Path,
    *,
    prefix: str | None = None,
) -> dict[str, Path]:
    """Draw publication-style base maps without task, graph, or route overlays."""
    preview = read_json(preview_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    configure_scientific_style()

    roi = preview.get("roi") or {}
    extent_km = float(roi.get("extent_km", 0.0))
    if extent_km <= 0.0:
        raise ValueError("preview ROI must define a positive extent_km")
    layers = preview.get("preview_layers") or {}
    available = _available_basemap_layers(layers)
    if not available:
        raise ValueError("preview does not contain any supported base-map layers")

    stem = prefix or Path(preview_path).stem
    title_prefix = f"Lunar south-pole {extent_km:g} km x {extent_km:g} km"
    extent = (0.0, extent_km, 0.0, extent_km)
    written: dict[str, Path] = {}

    columns = 2 if len(available) > 1 else 1
    rows = (len(available) + columns - 1) // columns
    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(10.2, 4.4 * rows),
        constrained_layout=True,
        squeeze=False,
    )
    flat_axes = list(axes.flat)
    for ax, layer_name in zip(flat_axes, available):
        image = _draw_preview_layer(ax, layers[layer_name], extent, layer_name)
        _format_preview_axes(ax, BASEMAP_LAYER_STYLE[layer_name]["title"], extent_km)
        _add_scale_bar(ax, extent)
        cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
        cbar.set_label(BASEMAP_LAYER_STYLE[layer_name]["colorbar"])
    for ax in flat_axes[len(available) :]:
        ax.set_visible(False)
    fig.suptitle(f"{title_prefix} real-raster terrain atlas", fontsize=11)
    atlas_path = output / f"{stem}_terrain_atlas.png"
    _save_png_pdf(fig, atlas_path)
    written["terrain_atlas_png"] = atlas_path
    written["terrain_atlas_pdf"] = atlas_path.with_suffix(".pdf")

    for layer_name in available:
        style = BASEMAP_LAYER_STYLE[layer_name]
        fig, ax = plt.subplots(figsize=(8.2, 7.4), constrained_layout=True)
        image = _draw_preview_layer(ax, layers[layer_name], extent, layer_name)
        _format_preview_axes(ax, f"{title_prefix} {style['title'].lower()}", extent_km)
        _add_scale_bar(ax, extent)
        cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
        cbar.set_label(style["colorbar"])
        suffix = {
            "elevation_m": "dem_basemap",
            "risk_index": "risk_basemap",
            "resource_index": "resource_basemap",
            "illumination_index": "illumination_basemap",
        }[layer_name]
        layer_path = output / f"{stem}_{suffix}.png"
        _save_png_pdf(fig, layer_path)
        written[f"{suffix}_png"] = layer_path
        written[f"{suffix}_pdf"] = layer_path.with_suffix(".pdf")
    return written


def draw_task_site_map(
    instance_path: str | Path,
    output_path: str | Path,
    *,
    preview_path: str | Path | None = None,
    label_tasks: bool = False,
) -> Path:
    """Draw task sites and the depot over the water-ice resource base map."""
    instance = read_json(instance_path)
    preview = read_json(preview_path) if preview_path else None
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    configure_scientific_style()

    extent = _extent(instance)
    extent_km = extent[1] - extent[0]
    resource = _resource_preview_matrix(instance, preview)
    tasks = list((instance.get("tasks") or {}).values())
    if not tasks:
        raise ValueError("instance does not contain any tasks")

    fig, ax = plt.subplots(figsize=(8.2, 7.4), constrained_layout=True)
    image = _draw_preview_layer(ax, resource, extent, "resource_index")
    ax.scatter(
        [float(task["xy_km"][0]) for task in tasks],
        [float(task["xy_km"][1]) for task in tasks],
        s=34,
        c="#f6e85f",
        edgecolors="black",
        linewidths=0.48,
        marker="o",
        label=f"task sites (n={len(tasks)})",
        zorder=6,
    )
    depot = instance["depot"]
    depot_xy = depot["xy_km"]
    ax.scatter(
        [float(depot_xy[0])],
        [float(depot_xy[1])],
        s=125,
        c="#53d7a3",
        edgecolors="black",
        linewidths=0.9,
        marker="*",
        label="depot",
        zorder=8,
    )
    if label_tasks:
        for task in tasks:
            task_id = str(task.get("id", ""))
            ax.text(
                float(task["xy_km"][0]) + 0.18,
                float(task["xy_km"][1]) + 0.18,
                task_id.rsplit("_", 1)[-1],
                fontsize=6.5,
                color="white",
                bbox={"facecolor": "black", "alpha": 0.45, "edgecolor": "none", "pad": 0.9},
                zorder=9,
            )
    seed = instance.get("seed", "unknown")
    _format_preview_axes(
        ax,
        f"Lunar south-pole {len(tasks)}-task operational instance, seed={seed}",
        extent_km,
    )
    _add_scale_bar(ax, extent)
    ax.legend(loc="upper right", frameon=True, framealpha=0.88)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("resource index")
    _save_png_pdf(fig, output)
    return output


def draw_logical_task_graph(
    instance_path: str | Path,
    output_path: str | Path,
    *,
    preview_path: str | Path | None = None,
) -> Path:
    instance = read_json(instance_path)
    preview = read_json(preview_path) if preview_path else None
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    configure_scientific_style()
    extent = _extent(instance)
    node_by_id = _node_by_id(instance)
    edge_by_pair = _best_undirected_edges(instance)
    costs = np.asarray([edge["generalized_cost"] for edge in edge_by_pair.values()], dtype="float64")
    cost_min = float(np.min(costs)) if costs.size else 0.0
    cost_max = float(np.max(costs)) if costs.size else 1.0
    cmap = mpl.colormaps.get_cmap("viridis")

    fig, ax = plt.subplots(figsize=(8.6, 8.2), constrained_layout=True)
    image = _draw_resource_background(ax, instance, extent, preview=preview)
    for edge in edge_by_pair.values():
        origin = node_by_id[edge["from"]]
        target = node_by_id[edge["to"]]
        scale = 0.0 if cost_max <= cost_min else (edge["generalized_cost"] - cost_min) / (cost_max - cost_min)
        ax.plot(
            [origin[0], target[0]],
            [origin[1], target[1]],
            color=cmap(scale),
            alpha=0.36,
            lw=0.82,
            zorder=2,
        )
    _draw_nodes(ax, instance, label_tasks=True)
    _format_axes(ax, instance, f"{instance['instance_id']} logical task graph")
    _add_scale_bar(ax, extent)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("resource index")
    norm = mpl.colors.Normalize(vmin=cost_min, vmax=cost_max)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    edge_cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.055, pad=0.08)
    edge_cbar.set_label("logical edge generalized cost")
    _save_png_pdf(fig, output)
    return output


def draw_path_option_overlay(
    instance_path: str | Path,
    output_path: str | Path,
    *,
    solution_path: str | Path | None = None,
    preview_path: str | Path | None = None,
) -> Path:
    instance = read_json(instance_path)
    solution = read_json(solution_path) if solution_path else None
    preview = read_json(preview_path) if preview_path else None
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    configure_scientific_style()
    extent = _extent(instance)
    fig, ax = plt.subplots(figsize=(8.6, 7.6), constrained_layout=True)
    image = _draw_resource_background(ax, instance, extent, preview=preview)
    legend_seen: set[str] = set()
    for edge in sorted(instance["logical_graph"]["edges"], key=lambda item: (item["from"], item["to"])):
        for option in edge.get("path_options", []):
            points = np.asarray(option.get("path_xy", []), dtype="float64")
            if points.shape[0] < 2:
                continue
            path_type = str(option["path_type"])
            style = PATH_STYLE.get(path_type, {"color": "white", "lw": 1.0, "alpha": 0.5})
            label = path_type if path_type not in legend_seen else None
            legend_seen.add(path_type)
            ax.plot(points[:, 0], points[:, 1], zorder=3, label=label, **style)
    if solution:
        edge_lookup = {
            (edge["from"], edge["to"], option["path_type"]): option
            for edge in instance["logical_graph"]["edges"]
            for option in edge.get("path_options", [])
        }
        for journey in solution.get("journeys", []):
            for sortie in journey.get("sorties", []):
                for leg in sortie.get("legs", []):
                    option = edge_lookup.get((leg["from"], leg["to"], leg.get("path_type", "low_risk")))
                    if not option:
                        continue
                    points = np.asarray(option.get("path_xy", []), dtype="float64")
                    if points.shape[0] >= 2:
                        ax.plot(points[:, 0], points[:, 1], color="#ffd166", lw=2.6, alpha=0.92, zorder=5)
    _draw_nodes(ax, instance, label_tasks=True)
    _format_axes(ax, instance, f"{instance['instance_id']} path option overlay")
    _add_scale_bar(ax, extent)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("resource index")
    handles, labels = ax.get_legend_handles_labels()
    if solution:
        handles.append(Line2D([0], [0], color="#ffd166", lw=2.6))
        labels.append("solution")
    ax.legend(handles, labels, loc="upper right", frameon=True, framealpha=0.88)
    _save_png_pdf(fig, output)
    return output


def _draw_resource_background(
    ax: plt.Axes,
    instance: dict[str, Any],
    extent: tuple[float, float, float, float],
    *,
    preview: dict[str, Any] | None,
) -> mpl.image.AxesImage:
    preview_matrix = _resource_preview_matrix(instance, preview)
    return ax.imshow(
        np.flipud(preview_matrix),
        extent=extent,
        origin="lower",
        cmap="magma",
        interpolation="bilinear" if preview_matrix.shape[0] >= 128 else "nearest",
        vmin=0.0,
        vmax=1.0,
    )


def _available_basemap_layers(layers: dict[str, Any]) -> list[str]:
    order = ("elevation_m", "risk_index", "resource_index", "illumination_index")
    available: list[str] = []
    expected_shape: tuple[int, int] | None = None
    for name in order:
        matrix = np.asarray(layers.get(name, []), dtype="float64")
        if matrix.ndim != 2 or matrix.size == 0:
            continue
        if expected_shape is None:
            expected_shape = matrix.shape
        elif matrix.shape != expected_shape:
            raise ValueError(
                f"base-map layer {name} has shape {matrix.shape}, expected {expected_shape}"
            )
        available.append(name)
    return available


def _draw_preview_layer(
    ax: plt.Axes,
    values: Any,
    extent: tuple[float, float, float, float],
    layer_name: str,
) -> mpl.image.AxesImage:
    style = BASEMAP_LAYER_STYLE[layer_name]
    matrix = np.asarray(values, dtype="float64")
    limits = style["limits"]
    vmin, vmax = limits if limits is not None else (None, None)
    return ax.imshow(
        np.flipud(np.ma.masked_invalid(matrix)),
        extent=extent,
        origin="lower",
        cmap=style["cmap"],
        interpolation="nearest",
        vmin=vmin,
        vmax=vmax,
    )


def _format_preview_axes(ax: plt.Axes, title: str, extent_km: float) -> None:
    ax.set_title(title)
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, extent_km)
    ax.set_ylim(0.0, extent_km)
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)


def _resource_preview_matrix(instance: dict[str, Any], preview: dict[str, Any] | None) -> np.ndarray:
    if preview:
        preview_layers = preview.get("preview_layers") or {}
        matrix = np.asarray(preview_layers.get("resource_index", []), dtype="float64")
        if matrix.size:
            return matrix
    matrix = np.asarray(instance["resource_map"].get("preview", []), dtype="float64")
    if matrix.size:
        return matrix
    return np.zeros((2, 2), dtype="float64")


def _draw_nodes(ax: plt.Axes, instance: dict[str, Any], *, label_tasks: bool) -> None:
    tasks = instance.get("tasks", {})
    for mode, color in MODE_COLOR.items():
        selected = [task for task in tasks.values() if task.get("operation_mode") == mode]
        if not selected:
            continue
        ax.scatter(
            [task["xy_km"][0] for task in selected],
            [task["xy_km"][1] for task in selected],
            s=42,
            c=color,
            edgecolors="black",
            linewidths=0.55,
            marker="o",
            label=mode,
            zorder=7,
        )
    depot = instance["depot"]["xy_km"]
    ax.scatter([depot[0]], [depot[1]], s=135, c="#53d7a3", edgecolors="black", linewidths=0.9, marker="*", label="depot", zorder=8)
    if label_tasks:
        for task_id, task in tasks.items():
            ax.text(
                float(task["xy_km"][0]) + 0.12,
                float(task["xy_km"][1]) + 0.12,
                task_id.rsplit("_", 1)[-1],
                fontsize=7,
                color="white",
                bbox={"facecolor": "black", "alpha": 0.42, "edgecolor": "none", "pad": 1.1},
                zorder=9,
            )


def _best_undirected_edges(instance: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in instance["logical_graph"]["edges"]:
        key = tuple(sorted((str(edge["from"]), str(edge["to"]))))
        options = edge.get("path_options", [])
        if not options:
            continue
        generalized = min(float(option["generalized_cost"]) for option in options)
        candidate = {"from": edge["from"], "to": edge["to"], "generalized_cost": generalized}
        if key not in best or generalized < float(best[key]["generalized_cost"]):
            best[key] = candidate
    return best


def _node_by_id(instance: dict[str, Any]) -> dict[str, tuple[float, float]]:
    return {
        str(node["id"]): (float(node["xy_km"][0]), float(node["xy_km"][1]))
        for node in instance["logical_graph"]["nodes"]
    }


def _extent(instance: dict[str, Any]) -> tuple[float, float, float, float]:
    extent_km = float(instance["resource_map"]["extent_km"])
    return (0.0, extent_km, 0.0, extent_km)


def _format_axes(ax: plt.Axes, instance: dict[str, Any], title: str) -> None:
    extent_km = float(instance["resource_map"]["extent_km"])
    ax.set_title(title)
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, extent_km)
    ax.set_ylim(0.0, extent_km)
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)


def _add_scale_bar(ax: plt.Axes, extent: tuple[float, float, float, float]) -> None:
    width_km = extent[1] - extent[0]
    height_km = extent[3] - extent[2]
    length = 5.0
    x0 = 0.08 * width_km
    y0 = 0.08 * height_km
    ax.plot([x0, x0 + length], [y0, y0], color="white", lw=3.0, solid_capstyle="butt", zorder=10)
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=1.0, solid_capstyle="butt", zorder=11)
    ax.text(
        x0 + length / 2.0,
        y0 + 0.35,
        "5 km",
        ha="center",
        va="bottom",
        color="black",
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none", "pad": 1.5},
        zorder=12,
    )


def _save_png_pdf(fig: plt.Figure, output_path: Path) -> None:
    png_path = output_path.with_suffix(".png")
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    if output_path.suffix.lower() not in {".png", ".pdf"}:
        fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)

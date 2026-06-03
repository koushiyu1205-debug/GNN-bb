"""Draw Moon Trek terrain/risk figures and sample operational scenarios."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from collections import deque
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np


@dataclass(frozen=True)
class TerrainGrid:
    dem: np.ndarray
    slope: np.ndarray
    roughness: np.ndarray
    risk: np.ndarray
    impassable: np.ndarray
    valid: np.ndarray
    width_km: float
    height_km: float
    source_dir: Path

    @property
    def shape(self) -> tuple[int, int]:
        return self.dem.shape


@dataclass(frozen=True)
class ScenarioConfig:
    seed: int = 7
    task_count: int = 20
    operation_radius_km: float = 10.0
    depot_xy_km: tuple[float, float] = (10.0, 10.0)
    vehicle_max_roundtrip_km: float = 30.0
    max_task_risk: float = 0.90
    min_point_spacing_km: float = 0.35


def load_terrain_grid(root: str | Path = "BPC_future/data/moon_trek/apollo15_20km") -> TerrainGrid:
    root_path = Path(root)
    grid_path = root_path / "processed" / "risk_grid.npz"
    bbox_path = root_path / "metadata" / "bbox.json"
    if not grid_path.exists():
        raise FileNotFoundError(f"risk grid not found: {grid_path}")
    if not bbox_path.exists():
        raise FileNotFoundError(f"bbox metadata not found: {bbox_path}")
    data = np.load(grid_path)
    bbox = json.loads(bbox_path.read_text(encoding="utf-8"))
    patch = bbox.get("patch", {})
    return TerrainGrid(
        dem=data["dem"].astype("float32"),
        slope=data["slope"].astype("float32"),
        roughness=data["roughness"].astype("float32"),
        risk=data["risk"].astype("float32"),
        impassable=data["impassable"].astype(bool),
        valid=data["valid"].astype(bool),
        width_km=float(patch.get("width_km", 20.0)),
        height_km=float(patch.get("height_km", 20.0)),
        source_dir=root_path,
    )


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


def draw_terrain_atlas(grid: TerrainGrid, output_dir: str | Path) -> dict[str, str]:
    configure_scientific_style()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = _figure_prefix(grid)
    extent = (0.0, grid.width_km, 0.0, grid.height_km)
    valid_dem = np.where(grid.valid, grid.dem, np.nan)
    valid_slope = np.where(grid.valid, grid.slope, np.nan)
    valid_risk = np.where(grid.valid, grid.risk, np.nan)
    valid_roughness = np.where(grid.valid, grid.roughness, np.nan)

    fig, axes = plt.subplots(2, 2, figsize=(10.2, 8.2), constrained_layout=True)
    panels = [
        (axes[0, 0], valid_dem, "DEM elevation", "terrain", "m"),
        (axes[0, 1], valid_slope, "Slope", "viridis", "deg"),
        (axes[1, 0], valid_risk, "Deterministic risk", "magma", "risk"),
        (axes[1, 1], valid_roughness, "Local roughness", "cividis", "m"),
    ]
    for ax, values, title, cmap, label in panels:
        image = ax.imshow(np.flipud(values), extent=extent, origin="lower", cmap=cmap, interpolation="nearest")
        _draw_impassable_contour(ax, grid)
        _format_map_axes(ax, title)
        cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
        cbar.set_label(label)
    _add_scale_bar(axes[1, 0], grid.width_km, grid.height_km)
    png = out / f"{prefix}_terrain_atlas.png"
    pdf = out / f"{prefix}_terrain_atlas.pdf"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.0, 7.0), constrained_layout=True)
    image = ax.imshow(np.flipud(valid_risk), extent=extent, origin="lower", cmap="magma", interpolation="nearest", vmin=0.0, vmax=1.0)
    _draw_impassable_contour(ax, grid)
    _format_map_axes(ax, f"{grid.source_dir.name} deterministic traversal risk")
    _add_scale_bar(ax, grid.width_km, grid.height_km)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("risk")
    risk_png = out / f"{prefix}_risk_map.png"
    risk_pdf = out / f"{prefix}_risk_map.pdf"
    fig.savefig(risk_png, bbox_inches="tight")
    fig.savefig(risk_pdf, bbox_inches="tight")
    plt.close(fig)

    pass_png, pass_pdf = draw_passability_map(grid, None, out)
    return {
        "terrain_atlas_png": str(png),
        "terrain_atlas_pdf": str(pdf),
        "risk_map_png": str(risk_png),
        "risk_map_pdf": str(risk_pdf),
        "passability_map_png": str(pass_png),
        "passability_map_pdf": str(pass_pdf),
    }


def draw_passability_map(grid: TerrainGrid, scenario: dict[str, Any] | None, output_dir: str | Path) -> tuple[Path, Path]:
    configure_scientific_style()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = _figure_prefix(grid)
    extent = (0.0, grid.width_km, 0.0, grid.height_km)
    passable = grid.valid & (~grid.impassable) & np.isfinite(grid.risk)
    passability = np.full(grid.shape, np.nan, dtype="float32")
    passability[grid.valid & grid.impassable] = 0.0
    passability[passable] = 1.0
    fig, ax = plt.subplots(figsize=(8.2, 7.4), constrained_layout=True)
    cmap = mpl.colors.ListedColormap(["#1b1b1b", "#d8efe4"])
    norm = mpl.colors.BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)
    image = ax.imshow(np.flipud(passability), extent=extent, origin="lower", cmap=cmap, norm=norm, interpolation="nearest")
    _draw_impassable_contour(ax, grid)
    _format_map_axes(ax, "Passability map")
    _add_scale_bar(ax, grid.width_km, grid.height_km)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03, ticks=[0, 1])
    cbar.ax.set_yticklabels(["blocked", "passable"])
    if scenario is not None:
        region = scenario["operation_region"]
        center = tuple(region["center_xy_km"])
        ax.add_patch(Circle(center, float(region["radius_km"]), fill=False, ec="#258bd2", lw=2.0, label="10 km operation radius"))
        component = scenario.get("connectivity", {})
        if component.get("depot_component_cells"):
            ax.text(
                0.03,
                0.97,
                f"depot component: {component['depot_component_cells']:,} cells",
                transform=ax.transAxes,
                va="top",
                ha="left",
                bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none", "pad": 3.0},
            )
        depot_xy = tuple(scenario["depot"]["xy_km"])
        task_x = [task["xy_km"][0] for task in scenario["tasks"]]
        task_y = [task["xy_km"][1] for task in scenario["tasks"]]
        ax.scatter(task_x, task_y, s=30, c="#f4cf45", edgecolors="black", linewidths=0.45, marker="o", label="tasks", zorder=5)
        ax.scatter([depot_xy[0]], [depot_xy[1]], s=105, c="#30d17a", edgecolors="black", linewidths=0.8, marker="*", label="fixed depot", zorder=6)
        ax.legend(loc="upper right", frameon=True, framealpha=0.88)
    suffix = "" if scenario is None else f"_seed{scenario['seed']}"
    png = out / f"{prefix}_passability_map{suffix}.png"
    pdf = out / f"{prefix}_passability_map{suffix}.pdf"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return png, pdf


def sample_operational_scenario(grid: TerrainGrid, config: ScenarioConfig) -> dict[str, Any]:
    rng = np.random.default_rng(int(config.seed))
    center = tuple(float(value) for value in config.depot_xy_km)
    _validate_region_inside_patch(grid, center, config.operation_radius_km)
    passable = grid.valid & (~grid.impassable) & np.isfinite(grid.risk)
    depot_row, depot_col = _xy_to_nearest_row_col(grid, center)
    if not passable[depot_row, depot_col]:
        raise RuntimeError(
            f"fixed depot at {center} maps to blocked cell row={depot_row}, col={depot_col}; "
            "choose a passable depot or relax passability rules"
        )
    depot_component = _connected_component(passable, depot_row, depot_col)
    depot_xy = _row_col_to_xy(grid, depot_row, depot_col)

    max_one_way = float(config.vehicle_max_roundtrip_km) / 2.0
    task_mask = passable & (grid.risk <= float(config.max_task_risk))
    task_mask &= depot_component
    task_mask &= _circle_mask(grid, center, config.operation_radius_km)
    task_mask &= _circle_mask(grid, depot_xy, max_one_way)
    candidates = np.argwhere(task_mask)
    if candidates.shape[0] < config.task_count:
        raise RuntimeError(
            f"only {candidates.shape[0]} candidate task cells, need {config.task_count}; "
            "increase vehicle_max_roundtrip_km or relax risk thresholds"
        )
    tasks = _sample_spaced_points(grid, candidates, rng, config.task_count, config.min_point_spacing_km, depot_xy)
    farthest = max(_distance_km(depot_xy, task["xy_km"]) for task in tasks) if tasks else 0.0
    return {
        "seed": int(config.seed),
        "terrain": {
            "source_dir": str(grid.source_dir),
            "width_km": grid.width_km,
            "height_km": grid.height_km,
            "shape": list(grid.shape),
        },
        "operation_region": {
            "center_xy_km": [round(center[0], 6), round(center[1], 6)],
            "radius_km": float(config.operation_radius_km),
            "note": "The depot and operation circle center are fixed; only task points are randomized.",
        },
        "vehicle": {
            "max_roundtrip_km": float(config.vehicle_max_roundtrip_km),
            "max_one_way_euclidean_km": max_one_way,
            "farthest_depot_task_km": round(farthest, 6),
        },
        "connectivity": {
            "type": "4-connected passable grid component",
            "depot_component_cells": int(depot_component.sum()),
            "task_candidate_cells": int(task_mask.sum()),
            "all_tasks_in_depot_component": True,
        },
        "sampling": asdict(config),
        "depot": {
            **_point_payload(grid, depot_row, depot_col, "depot"),
            "requested_xy_km": [round(center[0], 6), round(center[1], 6)],
        },
        "tasks": tasks,
    }


def draw_operational_scenario(grid: TerrainGrid, scenario: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    configure_scientific_style()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = _figure_prefix(grid)
    extent = (0.0, grid.width_km, 0.0, grid.height_km)
    valid_risk = np.where(grid.valid, grid.risk, np.nan)
    fig, ax = plt.subplots(figsize=(8.2, 7.4), constrained_layout=True)
    image = ax.imshow(np.flipud(valid_risk), extent=extent, origin="lower", cmap="magma", interpolation="nearest", vmin=0.0, vmax=1.0)
    _draw_impassable_contour(ax, grid)
    region = scenario["operation_region"]
    center = tuple(region["center_xy_km"])
    ax.add_patch(Circle(center, float(region["radius_km"]), fill=False, ec="#35b6ff", lw=2.0, ls="-", label="10 km operation radius"))
    depot = scenario["depot"]
    depot_xy = tuple(depot["xy_km"])
    max_one_way = float(scenario["vehicle"]["max_one_way_euclidean_km"])
    ax.add_patch(Circle(depot_xy, max_one_way, fill=False, ec="#8bd346", lw=1.7, ls="--", label="vehicle one-way range"))
    task_x = [task["xy_km"][0] for task in scenario["tasks"]]
    task_y = [task["xy_km"][1] for task in scenario["tasks"]]
    ax.scatter(task_x, task_y, s=30, c="#f6e85f", edgecolors="black", linewidths=0.45, marker="o", label="tasks", zorder=5)
    ax.scatter([depot_xy[0]], [depot_xy[1]], s=105, c="#53d7a3", edgecolors="black", linewidths=0.8, marker="*", label="depot", zorder=6)
    _format_map_axes(ax, f"Sampled {len(scenario['tasks'])}-task operational region, seed={scenario['seed']}")
    _add_scale_bar(ax, grid.width_km, grid.height_km)
    ax.legend(loc="upper right", frameon=True, framealpha=0.88)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("risk")
    png = out / f"{prefix}_sample_scenario_seed{scenario['seed']}.png"
    pdf = out / f"{prefix}_sample_scenario_seed{scenario['seed']}.pdf"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    pass_png, pass_pdf = draw_passability_map(grid, scenario, out)
    return {
        "scenario_png": str(png),
        "scenario_pdf": str(pdf),
        "scenario_passability_png": str(pass_png),
        "scenario_passability_pdf": str(pass_pdf),
    }


def write_scenario(path: str | Path, scenario: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(scenario, indent=2, sort_keys=True), encoding="utf-8")


def _draw_impassable_contour(ax: plt.Axes, grid: TerrainGrid) -> None:
    mask = np.flipud(grid.impassable.astype(float))
    ax.contour(mask, levels=[0.5], extent=(0.0, grid.width_km, 0.0, grid.height_km), colors="#111111", linewidths=0.25, alpha=0.55)


def _format_map_axes(ax: plt.Axes, title: str) -> None:
    ax.set_title(title)
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, ax.get_images()[0].get_extent()[1])
    ax.set_ylim(0.0, ax.get_images()[0].get_extent()[3])
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)


def _add_scale_bar(ax: plt.Axes, width_km: float, height_km: float) -> None:
    length = 5.0
    x0 = 0.08 * width_km
    y0 = 0.08 * height_km
    ax.plot([x0, x0 + length], [y0, y0], color="white", lw=3.0, solid_capstyle="butt")
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=1.0, solid_capstyle="butt")
    ax.text(x0 + length / 2.0, y0 + 0.35, "5 km", ha="center", va="bottom", color="black", fontsize=8, bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none", "pad": 1.5})


def _validate_region_inside_patch(grid: TerrainGrid, center_xy: tuple[float, float], radius_km: float) -> None:
    if center_xy[0] - radius_km < -1.0e-9 or center_xy[0] + radius_km > grid.width_km + 1.0e-9:
        raise ValueError("operation circle exceeds terrain patch in x direction")
    if center_xy[1] - radius_km < -1.0e-9 or center_xy[1] + radius_km > grid.height_km + 1.0e-9:
        raise ValueError("operation circle exceeds terrain patch in y direction")


def _circle_mask(grid: TerrainGrid, center_xy: tuple[float, float], radius_km: float) -> np.ndarray:
    rows, cols = grid.shape
    y = grid.height_km - (np.arange(rows, dtype="float32") + 0.5) * grid.height_km / rows
    x = (np.arange(cols, dtype="float32") + 0.5) * grid.width_km / cols
    xx, yy = np.meshgrid(x, y)
    return (xx - center_xy[0]) ** 2 + (yy - center_xy[1]) ** 2 <= float(radius_km) ** 2


def _choice_row_col(candidates: np.ndarray, rng: np.random.Generator) -> tuple[int, int]:
    idx = int(rng.integers(0, candidates.shape[0]))
    return int(candidates[idx, 0]), int(candidates[idx, 1])


def _connected_component(passable: np.ndarray, start_row: int, start_col: int) -> np.ndarray:
    component = np.zeros(passable.shape, dtype=bool)
    if not passable[start_row, start_col]:
        return component
    rows, cols = passable.shape
    queue: deque[tuple[int, int]] = deque([(int(start_row), int(start_col))])
    component[start_row, start_col] = True
    while queue:
        row, col = queue.popleft()
        for n_row, n_col in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)):
            if 0 <= n_row < rows and 0 <= n_col < cols and passable[n_row, n_col] and not component[n_row, n_col]:
                component[n_row, n_col] = True
                queue.append((n_row, n_col))
    return component


def _sample_spaced_points(
    grid: TerrainGrid,
    candidates: np.ndarray,
    rng: np.random.Generator,
    count: int,
    min_spacing_km: float,
    depot_xy: tuple[float, float],
) -> list[dict[str, Any]]:
    order = rng.permutation(candidates.shape[0])
    selected: list[tuple[int, int, tuple[float, float]]] = []
    for idx in order:
        row, col = int(candidates[idx, 0]), int(candidates[idx, 1])
        xy = _row_col_to_xy(grid, row, col)
        if _distance_km(xy, depot_xy) < min_spacing_km:
            continue
        if all(_distance_km(xy, prev_xy) >= min_spacing_km for _prev_row, _prev_col, prev_xy in selected):
            selected.append((row, col, xy))
            if len(selected) == count:
                break
    if len(selected) < count:
        raise RuntimeError(f"sampled only {len(selected)} spaced tasks, need {count}; lower min_point_spacing_km")
    return [_point_payload(grid, row, col, f"task_{index + 1}") for index, (row, col, _xy) in enumerate(selected)]


def _row_col_to_xy(grid: TerrainGrid, row: int, col: int) -> tuple[float, float]:
    rows, cols = grid.shape
    x = (float(col) + 0.5) * grid.width_km / float(cols)
    y = grid.height_km - (float(row) + 0.5) * grid.height_km / float(rows)
    return (x, y)


def _xy_to_nearest_row_col(grid: TerrainGrid, xy: tuple[float, float]) -> tuple[int, int]:
    rows, cols = grid.shape
    col = int(round(float(xy[0]) / grid.width_km * cols - 0.5))
    row = int(round((grid.height_km - float(xy[1])) / grid.height_km * rows - 0.5))
    return max(0, min(rows - 1, row)), max(0, min(cols - 1, col))


def _point_payload(grid: TerrainGrid, row: int, col: int, point_id: str) -> dict[str, Any]:
    xy = _row_col_to_xy(grid, row, col)
    return {
        "id": point_id,
        "row": int(row),
        "col": int(col),
        "xy_km": [round(xy[0], 6), round(xy[1], 6)],
        "dem_m": float(grid.dem[row, col]),
        "slope_deg": float(grid.slope[row, col]),
        "roughness_m": float(grid.roughness[row, col]),
        "risk": float(grid.risk[row, col]),
        "impassable": bool(grid.impassable[row, col]),
    }


def _distance_km(a: tuple[float, float] | list[float], b: tuple[float, float] | list[float]) -> float:
    return float(np.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1])))


def _figure_prefix(grid: TerrainGrid) -> str:
    return grid.source_dir.name.replace(" ", "_")

"""Build deterministic physical-grid and logical-task graphs from terrain rasters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import heapq
import json
import math
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from BPC_future.draw.moon_trek_viz import TerrainGrid, configure_scientific_style, load_terrain_grid


@dataclass(frozen=True)
class TerrainGraphConfig:
    grid_size: int = 256
    min_valid_fraction: float = 0.60
    max_impassable_fraction: float = 0.40
    risk_weight: float = 2.0
    slope_weight: float = 1.5
    uphill_weight: float = 3.0
    base_speed_kmh: float = 6.0
    min_speed_kmh: float = 1.0
    energy_risk_weight: float = 1.5
    energy_uphill_weight: float = 8.0
    path_dedup_metric_rel_tol: float = 0.01
    path_dedup_jaccard_threshold: float = 0.98


@dataclass(frozen=True)
class CoarseTerrainGraph:
    dem: np.ndarray
    slope: np.ndarray
    risk: np.ndarray
    passable: np.ndarray
    valid_fraction: np.ndarray
    impassable_fraction: np.ndarray
    width_km: float
    height_km: float
    source_dir: Path
    config: TerrainGraphConfig

    @property
    def shape(self) -> tuple[int, int]:
        return self.dem.shape

    @property
    def dx_km(self) -> float:
        return self.width_km / float(self.shape[1])

    @property
    def dy_km(self) -> float:
        return self.height_km / float(self.shape[0])


def build_coarse_terrain_graph(grid: TerrainGrid, config: TerrainGraphConfig) -> CoarseTerrainGraph:
    rows, cols = grid.shape
    size = int(config.grid_size)
    if rows % size != 0 or cols % size != 0:
        raise ValueError(f"terrain shape {grid.shape} is not divisible by graph grid_size={size}")
    row_factor = rows // size
    col_factor = cols // size
    valid = grid.valid & np.isfinite(grid.dem) & np.isfinite(grid.slope) & np.isfinite(grid.risk)
    impassable = grid.impassable | (~valid)
    valid_fraction = _block_mean(valid.astype("float32"), row_factor, col_factor)
    impassable_fraction = _block_mean(impassable.astype("float32"), row_factor, col_factor)
    passable = (valid_fraction >= float(config.min_valid_fraction)) & (
        impassable_fraction <= float(config.max_impassable_fraction)
    )
    dem = _block_nanmean(np.where(valid, grid.dem, np.nan), row_factor, col_factor)
    slope = _block_nanmean(np.where(valid, grid.slope, np.nan), row_factor, col_factor)
    risk = _block_nanmean(np.where(valid, grid.risk, np.nan), row_factor, col_factor)
    passable &= np.isfinite(dem) & np.isfinite(slope) & np.isfinite(risk)
    return CoarseTerrainGraph(
        dem=dem.astype("float32"),
        slope=slope.astype("float32"),
        risk=np.clip(risk, 0.0, 1.0).astype("float32"),
        passable=passable,
        valid_fraction=valid_fraction.astype("float32"),
        impassable_fraction=impassable_fraction.astype("float32"),
        width_km=grid.width_km,
        height_km=grid.height_km,
        source_dir=grid.source_dir,
        config=config,
    )


def build_logical_graph_payload(
    terrain_dir: str | Path,
    scenario_path: str | Path,
    *,
    config: TerrainGraphConfig = TerrainGraphConfig(),
) -> dict[str, Any]:
    grid = load_terrain_grid(terrain_dir)
    scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    graph = build_coarse_terrain_graph(grid, config)
    return build_logical_graph_payload_from_graph(
        graph,
        scenario,
        scenario_path=scenario_path,
        source_shape=grid.shape,
    )


def build_logical_graph_payload_from_graph(
    graph: CoarseTerrainGraph,
    scenario: dict[str, Any],
    *,
    scenario_path: str | Path | None = None,
    source_shape: tuple[int, int] | None = None,
) -> dict[str, Any]:
    nodes = _logical_nodes(graph, scenario)
    edges: list[dict[str, Any]] = []
    shortest_path_objectives = (
        ("low_time", "travel_time_h"),
        ("low_energy", "energy_proxy"),
        ("low_risk", "risk_integral"),
    )
    for origin in nodes:
        target_cells = {
            (int(target["row"]), int(target["col"]))
            for target in nodes
            if target["id"] != origin["id"]
        }
        search_results = {
            path_type: _dijkstra(graph, (origin["row"], origin["col"]), objective, targets=target_cells)
            for path_type, objective in shortest_path_objectives
        }
        for target in nodes:
            if target["id"] == origin["id"]:
                continue
            target_cell = (target["row"], target["col"])
            options: list[dict[str, Any]] = []
            for path_type, objective in shortest_path_objectives:
                distances, previous, metrics = search_results[path_type]
                target_index = target_cell[0] * graph.shape[1] + target_cell[1]
                if not np.isfinite(distances[target_cell]):
                    continue
                path = _reconstruct_path(previous, graph.shape, target_cell)
                metric = metrics[target_index]
                option = _path_option_payload(graph, path, metric, path_type, objective)
                _append_unique_path_option(options, option, graph.config)
            if not options:
                edge = {
                    "from": origin["id"],
                    "to": target["id"],
                    "feasible": False,
                    "reason": "no passable physical path on coarse graph",
                }
                edges.append(edge)
                continue
            best = min(options, key=lambda item: (item["generalized_cost"], item["path_type"]))
            edge = {
                "from": origin["id"],
                "to": target["id"],
                "feasible": True,
                "option_count": int(len(options)),
                "best_option_by_generalized_cost": best["path_type"],
                "generalized_cost": best["generalized_cost"],
                "path_distance_km": best["path_distance_km"],
                "risk_integral": best["risk_integral"],
                "energy_proxy": best["energy_proxy"],
                "travel_time_min": best["travel_time_min"],
                "euclidean_distance_km": round(_distance(origin["xy_km"], target["xy_km"]), 6),
                "path_options": options,
            }
            edges.append(edge)
    return {
        "terrain": {
            "source_dir": str(graph.source_dir),
            "scenario_path": "" if scenario_path is None else str(Path(scenario_path)),
            "width_km": graph.width_km,
            "height_km": graph.height_km,
            "source_shape": list(source_shape or graph.shape),
        },
        "physical_graph": {
            "type": "implicit 8-neighbor passable raster graph",
            "grid_size": int(graph.config.grid_size),
            "node_count": int(np.prod(graph.shape)),
            "passable_node_count": int(graph.passable.sum()),
            "blocked_node_count": int((~graph.passable).sum()),
            "approx_undirected_edge_count": int(_count_undirected_edges(graph.passable)),
            "dx_km": graph.dx_km,
            "dy_km": graph.dy_km,
            "config": asdict(graph.config),
        },
        "logical_graph": {
            "node_count": len(nodes),
            "directed_edge_count": len(edges),
            "feasible_directed_edge_count": sum(1 for edge in edges if edge.get("feasible")),
            "nodes": nodes,
            "edges": edges,
        },
        "scenario": {
            "seed": scenario.get("seed"),
            "operation_region": scenario.get("operation_region"),
            "vehicle": scenario.get("vehicle"),
        },
    }


def write_logical_graph(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def draw_physical_grid_graph(payload: dict[str, Any], output_path: str | Path) -> None:
    terrain = load_terrain_grid(payload["terrain"]["source_dir"])
    config = TerrainGraphConfig(**payload["physical_graph"]["config"])
    graph = build_coarse_terrain_graph(terrain, config)
    nodes = payload["logical_graph"]["nodes"]
    configure_scientific_style()
    extent = (0.0, graph.width_km, 0.0, graph.height_km)
    risk = np.where(graph.passable, graph.risk, np.nan)
    blocked = np.ma.masked_where(graph.passable, np.ones(graph.shape))
    fig, ax = plt.subplots(figsize=(8.4, 7.4), constrained_layout=True)
    image = ax.imshow(np.flipud(risk), extent=extent, origin="lower", cmap="magma", vmin=0.0, vmax=1.0)
    ax.imshow(np.flipud(blocked), extent=extent, origin="lower", cmap=mpl.colors.ListedColormap(["#111111"]), alpha=0.72)
    _draw_sparse_grid_edges(ax, graph, stride=max(4, graph.shape[0] // 32))
    _draw_logical_points(ax, nodes)
    ax.set_title(f"{Path(payload['terrain']['source_dir']).name} physical 8-neighbor grid graph")
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, graph.width_km)
    ax.set_ylim(0.0, graph.height_km)
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("mean cell risk")
    _save_png_pdf(fig, output_path)


def draw_logical_task_graph(payload: dict[str, Any], output_path: str | Path) -> None:
    terrain = load_terrain_grid(payload["terrain"]["source_dir"])
    nodes = payload["logical_graph"]["nodes"]
    edges = [edge for edge in payload["logical_graph"]["edges"] if edge.get("feasible")]
    undirected: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in edges:
        key = tuple(sorted((edge["from"], edge["to"])))
        if key not in undirected or edge["generalized_cost"] < undirected[key]["generalized_cost"]:
            undirected[key] = edge
    costs = np.array([edge["generalized_cost"] for edge in undirected.values()], dtype="float64")
    cost_min = float(np.min(costs)) if costs.size else 0.0
    cost_max = float(np.max(costs)) if costs.size else 1.0
    node_by_id = {node["id"]: node for node in nodes}
    configure_scientific_style()
    extent = (0.0, terrain.width_km, 0.0, terrain.height_km)
    risk = np.where(terrain.valid, terrain.risk, np.nan)
    fig, ax = plt.subplots(figsize=(8.6, 8.2), constrained_layout=True)
    image = ax.imshow(np.flipud(risk), extent=extent, origin="lower", cmap="magma", vmin=0.0, vmax=1.0)
    cmap = mpl.cm.get_cmap("viridis")
    for edge in undirected.values():
        origin = node_by_id[edge["from"]]
        target = node_by_id[edge["to"]]
        scale = 0.0 if cost_max <= cost_min else (edge["generalized_cost"] - cost_min) / (cost_max - cost_min)
        ax.plot(
            [origin["xy_km"][0], target["xy_km"][0]],
            [origin["xy_km"][1], target["xy_km"][1]],
            color=cmap(scale),
            alpha=0.20,
            lw=0.65,
            zorder=2,
        )
    _draw_logical_points(ax, nodes, label_tasks=True)
    ax.set_title(f"{Path(payload['terrain']['source_dir']).name} logical task graph")
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, terrain.width_km)
    ax.set_ylim(0.0, terrain.height_km)
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("risk")
    norm = mpl.colors.Normalize(vmin=cost_min, vmax=cost_max)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    edge_cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.055, pad=0.08)
    edge_cbar.set_label("logical edge generalized cost")
    _save_png_pdf(fig, output_path)


def draw_path_option_overlay(payload: dict[str, Any], output_path: str | Path) -> None:
    terrain = load_terrain_grid(payload["terrain"]["source_dir"])
    nodes = payload["logical_graph"]["nodes"]
    edges = [edge for edge in payload["logical_graph"]["edges"] if edge.get("feasible")]
    configure_scientific_style()
    extent = (0.0, terrain.width_km, 0.0, terrain.height_km)
    risk = np.where(terrain.valid, terrain.risk, np.nan)
    fig, ax = plt.subplots(figsize=(8.6, 7.6), constrained_layout=True)
    image = ax.imshow(np.flipud(risk), extent=extent, origin="lower", cmap="magma", vmin=0.0, vmax=1.0)
    styles = {
        "low_time": {"color": "#32b8ff", "lw": 0.72, "alpha": 0.28},
        "low_energy": {"color": "#7bd34a", "lw": 0.64, "alpha": 0.25},
        "low_risk": {"color": "#ffb84c", "lw": 0.58, "alpha": 0.25},
    }
    legend_seen: set[str] = set()
    for edge in sorted(edges, key=lambda item: (item["from"], item["to"])):
        for option in edge.get("path_options", []):
            path_type = option["path_type"]
            points = np.array(option["path_xy"], dtype="float64")
            if points.shape[0] < 2:
                continue
            style = styles.get(path_type, {"color": "white", "lw": 1.0, "alpha": 0.6})
            label = path_type if path_type not in legend_seen else None
            legend_seen.add(path_type)
            ax.plot(points[:, 0], points[:, 1], zorder=4, label=label, **style)
    _draw_logical_points(ax, nodes, label_tasks=True)
    ax.set_title(f"{Path(payload['terrain']['source_dir']).name} physical path option overlay")
    ax.set_xlabel("east-west distance (km)")
    ax.set_ylabel("south-north distance (km)")
    ax.set_xlim(0.0, terrain.width_km)
    ax.set_ylim(0.0, terrain.height_km)
    ax.set_aspect("equal")
    ax.grid(color="white", alpha=0.12, linewidth=0.4)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("risk")
    ax.legend(loc="upper right", frameon=True, framealpha=0.86)
    _save_png_pdf(fig, output_path)


def _block_mean(values: np.ndarray, row_factor: int, col_factor: int) -> np.ndarray:
    rows, cols = values.shape
    return values.reshape(rows // row_factor, row_factor, cols // col_factor, col_factor).mean(axis=(1, 3))


def _block_nanmean(values: np.ndarray, row_factor: int, col_factor: int) -> np.ndarray:
    rows, cols = values.shape
    blocks = values.reshape(rows // row_factor, row_factor, cols // col_factor, col_factor)
    with np.errstate(all="ignore"):
        return np.nanmean(blocks, axis=(1, 3))


def _logical_nodes(graph: CoarseTerrainGraph, scenario: dict[str, Any]) -> list[dict[str, Any]]:
    raw_nodes = [scenario["depot"], *scenario["tasks"]]
    nodes: list[dict[str, Any]] = []
    for raw in raw_nodes:
        requested_xy = tuple(raw["xy_km"])
        row, col = _xy_to_row_col(graph, requested_xy)
        snapped_row, snapped_col = _nearest_passable_cell(graph.passable, row, col)
        snapped_xy = _row_col_to_xy(graph, snapped_row, snapped_col)
        nodes.append(
            {
                "id": raw["id"],
                "kind": "depot" if raw["id"] == "depot" else "task",
                "xy_km": [round(snapped_xy[0], 6), round(snapped_xy[1], 6)],
                "requested_xy_km": [round(float(requested_xy[0]), 6), round(float(requested_xy[1]), 6)],
                "row": int(snapped_row),
                "col": int(snapped_col),
                "snap_distance_km": round(_distance(requested_xy, snapped_xy), 6),
                "risk": float(graph.risk[snapped_row, snapped_col]),
                "slope_deg": float(graph.slope[snapped_row, snapped_col]),
                "dem_m": float(graph.dem[snapped_row, snapped_col]),
            }
        )
    return nodes


def _dijkstra(
    graph: CoarseTerrainGraph,
    source: tuple[int, int],
    objective: str,
    targets: set[tuple[int, int]] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows, cols = graph.shape
    distances = np.full(graph.shape, np.inf, dtype="float64")
    previous = np.full((rows * cols,), -1, dtype="int64")
    metrics = np.zeros((rows * cols, 5), dtype="float64")
    if not graph.passable[source]:
        return distances, previous, metrics
    remaining_targets = set(targets or ())
    remaining_targets.discard(source)
    distances[source] = 0.0
    heap: list[tuple[float, int, int]] = [(0.0, int(source[0]), int(source[1]))]
    while heap:
        current, row, col = heapq.heappop(heap)
        if current != distances[row, col]:
            continue
        if remaining_targets and (row, col) in remaining_targets:
            remaining_targets.remove((row, col))
            if not remaining_targets:
                break
        current_index = row * cols + col
        for n_row, n_col, step_distance in _neighbors(graph, row, col):
            edge = _edge_metrics(graph, row, col, n_row, n_col, step_distance)
            objective_value = _objective_value(edge, objective)
            next_value = current + objective_value
            if next_value < distances[n_row, n_col]:
                distances[n_row, n_col] = next_value
                next_index = n_row * cols + n_col
                previous[next_index] = current_index
                metrics[next_index] = metrics[current_index] + np.array(
                    [
                        edge["distance_km"],
                        edge["risk_integral"],
                        edge["energy_proxy"],
                        edge["travel_time_h"],
                        edge["generalized_cost"],
                    ],
                    dtype="float64",
                )
                heapq.heappush(heap, (next_value, n_row, n_col))
    return distances, previous, metrics


def _neighbors(graph: CoarseTerrainGraph, row: int, col: int):
    for row_delta in (-1, 0, 1):
        for col_delta in (-1, 0, 1):
            if row_delta == 0 and col_delta == 0:
                continue
            n_row = row + row_delta
            n_col = col + col_delta
            if not (0 <= n_row < graph.shape[0] and 0 <= n_col < graph.shape[1]):
                continue
            if not graph.passable[n_row, n_col]:
                continue
            # Avoid diagonal corner cutting through two blocked orthogonal cells.
            if row_delta != 0 and col_delta != 0:
                if not graph.passable[row, n_col] or not graph.passable[n_row, col]:
                    continue
            step = math.hypot(float(col_delta) * graph.dx_km, float(row_delta) * graph.dy_km)
            yield n_row, n_col, step


def _edge_metrics(
    graph: CoarseTerrainGraph,
    row: int,
    col: int,
    n_row: int,
    n_col: int,
    distance_km: float,
) -> dict[str, float]:
    avg_risk = 0.5 * (float(graph.risk[row, col]) + float(graph.risk[n_row, n_col]))
    avg_slope = 0.5 * (float(graph.slope[row, col]) + float(graph.slope[n_row, n_col]))
    elevation_delta = float(graph.dem[n_row, n_col]) - float(graph.dem[row, col])
    uphill_grade = max(0.0, elevation_delta / max(distance_km * 1000.0, 1.0))
    slope_penalty = (avg_slope / 30.0) ** 2
    generalized = distance_km * (
        1.0
        + graph.config.risk_weight * avg_risk
        + graph.config.slope_weight * slope_penalty
        + graph.config.uphill_weight * uphill_grade
    )
    speed = graph.config.base_speed_kmh / (1.0 + 1.5 * avg_risk + 2.0 * slope_penalty + 2.0 * uphill_grade)
    speed = max(float(graph.config.min_speed_kmh), float(speed))
    time_h = distance_km / speed
    energy = distance_km * (
        1.0
        + graph.config.energy_risk_weight * avg_risk
        + graph.config.energy_uphill_weight * uphill_grade
        + slope_penalty
    )
    risk_integral = distance_km * avg_risk
    return {
        "generalized_cost": generalized,
        "distance_km": distance_km,
        "risk_integral": risk_integral,
        "energy_proxy": energy,
        "travel_time_h": time_h,
    }


def _objective_value(edge: dict[str, float], objective: str) -> float:
    if objective == "generalized_cost":
        return edge["generalized_cost"]
    if objective == "travel_time_h":
        return edge["travel_time_h"]
    if objective == "energy_proxy":
        return edge["energy_proxy"]
    if objective == "risk_integral":
        # Keep an infinitesimal distance term so zero-risk plateaus still
        # produce deterministic shortest paths instead of arbitrary wandering.
        return edge["risk_integral"] + 1.0e-6 * edge["distance_km"]
    raise ValueError(f"unknown terrain graph objective: {objective}")


def _path_option_payload(
    graph: CoarseTerrainGraph,
    path: list[tuple[int, int]],
    metric: np.ndarray,
    path_type: str,
    objective: str,
) -> dict[str, Any]:
    full_xy = _path_xy(graph, path)
    return {
        "path_type": path_type,
        "aliases": [path_type],
        "objective": objective,
        "generalized_cost": round(float(metric[4]), 6),
        "path_distance_km": round(float(metric[0]), 6),
        "risk_integral": round(float(metric[1]), 6),
        "energy_proxy": round(float(metric[2]), 6),
        "travel_time_min": round(float(metric[3] * 60.0), 6),
        "path_cell_count": int(len(path)),
        "path_cells": [[int(row), int(col)] for row, col in path],
        "path_xy": full_xy,
    }


def _append_unique_path_option(
    options: list[dict[str, Any]],
    option: dict[str, Any],
    config: TerrainGraphConfig,
) -> None:
    for existing in options:
        if _path_options_duplicate(existing, option, config):
            aliases = set(existing.get("aliases", []))
            aliases.update(option.get("aliases", []))
            aliases.add(option["path_type"])
            existing["aliases"] = sorted(aliases)
            existing["duplicate_path_types"] = sorted(
                set(existing.get("duplicate_path_types", [])) | {option["path_type"]}
            )
            return
    options.append(option)


def _path_options_duplicate(
    left: dict[str, Any],
    right: dict[str, Any],
    config: TerrainGraphConfig,
) -> bool:
    left_cells = {tuple(cell) for cell in left["path_cells"]}
    right_cells = {tuple(cell) for cell in right["path_cells"]}
    if left_cells == right_cells:
        return True
    intersection = len(left_cells & right_cells)
    union = max(len(left_cells | right_cells), 1)
    jaccard = float(intersection) / float(union)
    if jaccard < float(config.path_dedup_jaccard_threshold):
        return False
    metric_keys = ("path_distance_km", "risk_integral", "energy_proxy", "travel_time_min", "generalized_cost")
    for key in metric_keys:
        denominator = max(abs(float(left[key])), abs(float(right[key])), 1.0)
        if abs(float(left[key]) - float(right[key])) / denominator > float(config.path_dedup_metric_rel_tol):
            return False
    return True


def _reconstruct_path(previous: np.ndarray, shape: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    cols = shape[1]
    index = target[0] * cols + target[1]
    path: list[tuple[int, int]] = []
    while index >= 0:
        row, col = divmod(int(index), cols)
        path.append((row, col))
        index = int(previous[index])
    path.reverse()
    return path


def _path_sample_xy(graph: CoarseTerrainGraph, path: list[tuple[int, int]], max_points: int) -> list[list[float]]:
    if len(path) <= max_points:
        sample = path
    else:
        indices = np.linspace(0, len(path) - 1, max_points).round().astype(int)
        sample = [path[int(index)] for index in indices]
    return [[round(x, 6), round(y, 6)] for x, y in (_row_col_to_xy(graph, row, col) for row, col in sample)]


def _path_xy(graph: CoarseTerrainGraph, path: list[tuple[int, int]]) -> list[list[float]]:
    return [[round(x, 6), round(y, 6)] for x, y in (_row_col_to_xy(graph, row, col) for row, col in path)]


def _xy_to_row_col(graph: CoarseTerrainGraph, xy: tuple[float, float]) -> tuple[int, int]:
    col = int(round(float(xy[0]) / graph.width_km * graph.shape[1] - 0.5))
    row = int(round((graph.height_km - float(xy[1])) / graph.height_km * graph.shape[0] - 0.5))
    return max(0, min(graph.shape[0] - 1, row)), max(0, min(graph.shape[1] - 1, col))


def _row_col_to_xy(graph: CoarseTerrainGraph, row: int, col: int) -> tuple[float, float]:
    x = (float(col) + 0.5) * graph.width_km / float(graph.shape[1])
    y = graph.height_km - (float(row) + 0.5) * graph.height_km / float(graph.shape[0])
    return x, y


def _nearest_passable_cell(passable: np.ndarray, row: int, col: int) -> tuple[int, int]:
    if passable[row, col]:
        return row, col
    rows, cols = passable.shape
    best: tuple[float, int, int] | None = None
    for radius in range(1, max(rows, cols)):
        row_min = max(0, row - radius)
        row_max = min(rows - 1, row + radius)
        col_min = max(0, col - radius)
        col_max = min(cols - 1, col + radius)
        candidates: list[tuple[int, int]] = []
        for candidate_col in range(col_min, col_max + 1):
            candidates.append((row_min, candidate_col))
            candidates.append((row_max, candidate_col))
        for candidate_row in range(row_min + 1, row_max):
            candidates.append((candidate_row, col_min))
            candidates.append((candidate_row, col_max))
        for candidate_row, candidate_col in candidates:
            if passable[candidate_row, candidate_col]:
                dist = float((candidate_row - row) ** 2 + (candidate_col - col) ** 2)
                item = (dist, candidate_row, candidate_col)
                if best is None or item < best:
                    best = item
        if best is not None:
            return best[1], best[2]
    raise RuntimeError("no passable cell in coarse physical graph")


def _distance(a: list[float] | tuple[float, float], b: list[float] | tuple[float, float]) -> float:
    return float(math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1])))


def _count_undirected_edges(passable: np.ndarray) -> int:
    count = 0
    rows, cols = passable.shape
    for row in range(rows):
        for col in range(cols):
            if not passable[row, col]:
                continue
            for row_delta, col_delta in ((0, 1), (1, 0), (1, 1), (1, -1)):
                n_row = row + row_delta
                n_col = col + col_delta
                if 0 <= n_row < rows and 0 <= n_col < cols and passable[n_row, n_col]:
                    count += 1
    return count


def _draw_sparse_grid_edges(ax: plt.Axes, graph: CoarseTerrainGraph, stride: int) -> None:
    color = "#c7d4dc"
    for row in range(0, graph.shape[0], stride):
        y = graph.height_km - (float(row) + 0.5) * graph.dy_km
        segments: list[tuple[float, float]] = []
        start: float | None = None
        prev_x: float | None = None
        for col in range(graph.shape[1]):
            if graph.passable[row, col]:
                x = (float(col) + 0.5) * graph.dx_km
                if start is None:
                    start = x
                prev_x = x
            elif start is not None and prev_x is not None:
                segments.append((start, prev_x))
                start = None
                prev_x = None
        if start is not None and prev_x is not None:
            segments.append((start, prev_x))
        for x0, x1 in segments:
            ax.plot([x0, x1], [y, y], color=color, alpha=0.12, lw=0.3, zorder=1)
    for col in range(0, graph.shape[1], stride):
        x = (float(col) + 0.5) * graph.dx_km
        segments = []
        start = None
        prev_y = None
        for row in range(graph.shape[0]):
            if graph.passable[row, col]:
                y = graph.height_km - (float(row) + 0.5) * graph.dy_km
                if start is None:
                    start = y
                prev_y = y
            elif start is not None and prev_y is not None:
                segments.append((start, prev_y))
                start = None
                prev_y = None
        if start is not None and prev_y is not None:
            segments.append((start, prev_y))
        for y0, y1 in segments:
            ax.plot([x, x], [y0, y1], color=color, alpha=0.12, lw=0.3, zorder=1)


def _draw_logical_points(ax: plt.Axes, nodes: list[dict[str, Any]], *, label_tasks: bool = False) -> None:
    tasks = [node for node in nodes if node["kind"] == "task"]
    depot = next(node for node in nodes if node["kind"] == "depot")
    ax.scatter(
        [node["xy_km"][0] for node in tasks],
        [node["xy_km"][1] for node in tasks],
        s=32,
        c="#f4cf45",
        edgecolors="black",
        linewidths=0.45,
        marker="o",
        label="tasks",
        zorder=8,
    )
    ax.scatter(
        [depot["xy_km"][0]],
        [depot["xy_km"][1]],
        s=110,
        c="#30d17a",
        edgecolors="black",
        linewidths=0.8,
        marker="*",
        label="depot",
        zorder=9,
    )
    if label_tasks:
        for node in tasks:
            label = node["id"].removeprefix("task_")
            ax.text(node["xy_km"][0] + 0.08, node["xy_km"][1] + 0.08, label, color="white", fontsize=6, zorder=10)
    ax.legend(loc="upper right", frameon=True, framealpha=0.86)


def _draw_selected_physical_paths(ax: plt.Axes, edges: list[dict[str, Any]], node_by_id: dict[str, dict[str, Any]]) -> None:
    depot_edges = [edge for edge in edges if edge["from"] == "depot" and edge.get("path_xy_sample")]
    depot_edges = sorted(depot_edges, key=lambda edge: edge["generalized_cost"])[:8]
    for edge in depot_edges:
        points = np.array(edge["path_xy_sample"], dtype="float64")
        ax.plot(points[:, 0], points[:, 1], color="#6fe4ff", alpha=0.58, lw=1.15, zorder=4)


def _save_png_pdf(fig: plt.Figure, output_path: str | Path) -> None:
    png_path = Path(output_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(png_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)

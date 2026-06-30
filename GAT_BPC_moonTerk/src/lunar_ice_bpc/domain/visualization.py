"""Dependency-free SVG visualization for lunar-ice instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import math

from lunar_ice_bpc.io.instance_io import read_json


WONG_BLUE = "#2271B2"
WONG_CYAN = "#3DB7E9"
WONG_MAGENTA = "#F748A5"
WONG_GREEN = "#359B73"
WONG_ORANGE = "#D55E00"
WONG_GOLD = "#E69F00"
WONG_YELLOW = "#F0E442"

MODE_COLOR = {"detect": "#9BC3D4", "sample": "#7EA67E", "drill": WONG_ORANGE}
PATH_COLOR = {"low_time": "#5A91B1", "low_energy": "#6D9A72", "low_risk": "#C79A4A"}


def _scale_xy(x: float, y: float, extent: float, size: int, pad: int) -> tuple[float, float]:
    sx = pad + float(x) / float(extent) * (size - 2 * pad)
    sy = pad + (1.0 - float(y) / float(extent)) * (size - 2 * pad)
    return sx, sy


def _polyline(points: list[list[float]], extent: float, size: int, pad: int) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in (_scale_xy(p[0], p[1], extent, size, pad) for p in points))


def _edge_options(instance: dict[str, Any]) -> dict[tuple[str, str], dict[str, dict]]:
    edges: dict[tuple[str, str], dict[str, dict]] = {}
    for edge in instance.get("logical_graph", {}).get("edges", []):
        edges[(edge["from"], edge["to"])] = {option["path_type"]: option for option in edge.get("path_options", [])}
    return edges


def _logical_node_xy(instance: dict[str, Any]) -> dict[str, list[float]]:
    nodes: dict[str, list[float]] = {}
    for node in instance.get("logical_graph", {}).get("nodes", []):
        nodes[str(node["id"])] = [float(node["xy_km"][0]), float(node["xy_km"][1])]
    if not nodes:
        nodes["depot"] = [float(instance["depot"]["xy_km"][0]), float(instance["depot"]["xy_km"][1])]
        for task_id, task in instance.get("tasks", {}).items():
            nodes[str(task_id)] = [float(task["xy_km"][0]), float(task["xy_km"][1])]
    return nodes


def write_svg(
    instance_path: str | Path,
    output_path: str | Path,
    *,
    solution_path: str | Path | None = None,
    show_logical_edges: bool = True,
    path_preview: str = "all",
    background_mode: str = "resource",
    show_reference_solution: bool = False,
) -> Path:
    instance = read_json(instance_path)
    if solution_path:
        solution = read_json(solution_path)
    elif show_reference_solution:
        solution = instance.get("reference_solution", {})
    else:
        solution = {}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    size = 920
    pad = 55
    extent = float(instance["resource_map"]["extent_km"])
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#fffdf6"/>',
    ]
    preview, risk_preview, background_label = _background_layers(instance, background_mode=background_mode)
    cell_count = len(preview) or 1
    cell_size = (size - 2 * pad) / float(cell_count)
    for row, values in enumerate(preview):
        for col, value in enumerate(values):
            value = _clamp(float(value))
            if background_label == "DEM":
                color = _dem_color(value)
            else:
                risk = _clamp(float(risk_preview[row][col])) if risk_preview else 0.0
                color = _resource_risk_color(value, risk)
            x = pad + col * cell_size
            y = pad + row * cell_size
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size + 0.2:.2f}" height="{cell_size + 0.2:.2f}" fill="{color}"/>')
    parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="none" stroke="#202020" stroke-width="1.2"/>')
    edge_lookup = _edge_options(instance)
    node_xy = _logical_node_xy(instance)
    if show_logical_edges:
        drawn_pairs: set[tuple[str, str]] = set()
        for source, target in sorted(edge_lookup):
            pair = tuple(sorted((source, target)))
            if pair in drawn_pairs:
                continue
            drawn_pairs.add(pair)
            if source not in node_xy or target not in node_xy:
                continue
            x1, y1 = _scale_xy(node_xy[source][0], node_xy[source][1], extent, size, pad)
            x2, y2 = _scale_xy(node_xy[target][0], node_xy[target][1], extent, size, pad)
            parts.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                'stroke="#202020" stroke-width="0.55" opacity="0.18"/>'
            )
    tasks = instance["tasks"]
    if path_preview != "none":
        preview_edges = sorted(edge_lookup.items())
        if path_preview == "sample":
            first_tasks = set(list(tasks.keys())[: min(3, len(tasks))])
            preview_edges = [item for item in preview_edges if item[0][0] == "depot" and item[0][1] in first_tasks]
        elif path_preview != "all":
            raise ValueError(f"unsupported path_preview {path_preview!r}")
        for (_source, _target), options in preview_edges:
            for path_type, option in options.items():
                points = option.get("path_xy") or [node_xy[_source], node_xy[_target]]
                color = PATH_COLOR[path_type]
                parts.append(
                    f'<polyline points="{_polyline(points, extent, size, pad)}" fill="none" stroke="#202020" '
                    f'stroke-width="1.65" opacity="0.18"/>'
                )
                parts.append(
                    f'<polyline points="{_polyline(points, extent, size, pad)}" fill="none" stroke="{color}" '
                    f'stroke-width="1.25" opacity="0.50"/>'
                )
    for journey in solution.get("journeys", []):
        for sortie in journey.get("sorties", []):
            for leg in sortie.get("legs", []):
                option = edge_lookup.get((leg["from"], leg["to"]), {}).get(leg.get("path_type", "low_risk"))
                if not option:
                    continue
                parts.append(
                    f'<polyline points="{_polyline(option.get("path_xy", []), extent, size, pad)}" fill="none" '
                    f'stroke="#202020" stroke-width="3.4" opacity="0.45"/>'
                )
                parts.append(
                    f'<polyline points="{_polyline(option.get("path_xy", []), extent, size, pad)}" fill="none" '
                    f'stroke="{WONG_YELLOW}" stroke-width="2.8" opacity="0.96"/>'
                )
    depot_x, depot_y = _scale_xy(instance["depot"]["xy_km"][0], instance["depot"]["xy_km"][1], extent, size, pad)
    parts.append(_star_svg(depot_x, depot_y, outer=11.0, inner=4.3, fill=WONG_YELLOW, stroke="#202020", stroke_width=1.4))
    parts.append(f'<text x="{depot_x + 10:.2f}" y="{depot_y - 10:.2f}" fill="#111827" stroke="#fbfbf8" stroke-width="3" paint-order="stroke" font-size="14">depot</text>')
    for task_id, task in tasks.items():
        x, y = _scale_xy(task["xy_km"][0], task["xy_km"][1], extent, size, pad)
        color = MODE_COLOR.get(task.get("operation_mode"), "#e5e7eb")
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.8" fill="{color}" stroke="#202020" stroke-width="1.0"/>')
    has_solution_overlay = bool(solution.get("journeys"))
    has_path_options = path_preview != "none"
    if background_label == "DEM":
        _add_dem_legend(parts, x=size - pad - 218, y=pad + 14, show_paths=has_path_options, show_solution=has_solution_overlay)
    else:
        _add_resource_risk_legend(parts, x=size - pad - 234, y=pad + 14, show_paths=has_path_options, show_solution=has_solution_overlay)
    _add_svg_scale_bar(parts, size=size, pad=pad, extent=extent)
    status = solution.get("status", "solution") if has_solution_overlay else "instance"
    view_label = _view_label(show_logical_edges=show_logical_edges, path_preview=path_preview, has_solution_overlay=has_solution_overlay)
    title = f'{instance["instance_id"]} | {len(tasks)} targets | {background_label} | view={view_label} | status={status}'
    parts.append(f'<text x="{pad}" y="32" fill="#111827" font-size="18" font-family="monospace">{title}</text>')
    footer = _footer_text(show_logical_edges=show_logical_edges, path_preview=path_preview, has_solution_overlay=has_solution_overlay)
    parts.append(f'<text x="55" y="890" fill="#5a4326" font-size="13">{footer}</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def _background_layers(instance: dict[str, Any], *, background_mode: str) -> tuple[list[list[float]], list[list[float]], str]:
    resource = instance["resource_map"].get("preview", [])
    risk = instance["resource_map"].get("risk_preview", [])
    dem = instance["resource_map"].get("dem_preview", [])
    if background_mode == "dem" and dem:
        return dem, [], "DEM"
    if background_mode != "resource" and background_mode != "dem":
        raise ValueError(f"unsupported background_mode {background_mode!r}")
    return resource, risk, "resource/risk"


def _resource_risk_color(resource: float, risk: float) -> str:
    resource_v = _smoothstep(_clamp(resource))
    risk_v = _smoothstep(_clamp(risk))
    base = _blend_rgb((239, 222, 181), (219, 194, 151), 0.24 * risk_v)
    basin_blue = (92, 130, 151)
    ice_blue = (153, 184, 196)
    risk_warm = (190, 128, 98)
    color = _blend_rgb(base, basin_blue, 0.54 * resource_v)
    color = _blend_rgb(color, ice_blue, 0.22 * _smoothstep(resource_v))
    color = _blend_rgb(color, risk_warm, 0.17 * risk_v)
    return _rgb_hex(color)


def _dem_color(value: float) -> str:
    v = _clamp(value)
    if v < 0.34:
        return _rgb_hex(_blend_rgb((78, 111, 130), (137, 158, 156), _smoothstep(v / 0.34)))
    if v < 0.66:
        return _rgb_hex(_blend_rgb((137, 158, 156), (219, 197, 151), _smoothstep((v - 0.34) / 0.32)))
    if v < 0.86:
        return _rgb_hex(_blend_rgb((219, 197, 151), (203, 141, 111), _smoothstep((v - 0.66) / 0.20)))
    return _rgb_hex(_blend_rgb((203, 141, 111), (248, 234, 195), _smoothstep((v - 0.86) / 0.14)))


def _star_svg(x: float, y: float, *, outer: float, inner: float, fill: str, stroke: str, stroke_width: float) -> str:
    points = []
    for idx in range(16):
        angle = -math.pi / 2.0 + idx * math.pi / 8.0
        radius = outer if idx % 2 == 0 else inner
        points.append(f"{x + radius * math.cos(angle):.2f},{y + radius * math.sin(angle):.2f}")
    return f'<polygon points="{" ".join(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:.2f}"/>'


def _view_label(*, show_logical_edges: bool, path_preview: str, has_solution_overlay: bool) -> str:
    if has_solution_overlay:
        return "solution"
    if show_logical_edges and path_preview == "none":
        return "logical_graph"
    if not show_logical_edges and path_preview != "none":
        return "path_options"
    if not show_logical_edges and path_preview == "none":
        return "targets"
    return "combined"


def _footer_text(*, show_logical_edges: bool, path_preview: str, has_solution_overlay: bool) -> str:
    parts = []
    if show_logical_edges:
        parts.append("thin dark lines: complete logical graph")
    if path_preview != "none":
        parts.append("blue/green/amber: candidate path options")
    if has_solution_overlay:
        parts.append("yellow: reference/solution route")
    if not parts:
        return "targets only; no logical edges or path options are shown"
    return "; ".join(parts)


def _add_resource_risk_legend(
    parts: list[str],
    *,
    x: float,
    y: float,
    show_paths: bool = True,
    show_solution: bool = False,
) -> None:
    row_count = 3 + (3 if show_paths else 0) + (1 if show_solution else 0)
    height = 84 + 15 * row_count
    parts.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="224" height="{height}" rx="5" '
        'fill="#fff2cf" opacity="0.90" stroke="#7a5a2a" stroke-width="0.8"/>'
    )
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 21:.2f}" fill="#332719" font-size="12" font-weight="700">legend</text>')
    _add_colorbar(parts, x=x + 12, y=y + 35, width=126, height=10, color_at=lambda t: _resource_risk_color(t, 0.10))
    parts.append(f'<text x="{x + 145:.2f}" y="{y + 44:.2f}" fill="#332719" font-size="10">ice/resource</text>')
    _add_colorbar(parts, x=x + 12, y=y + 58, width=126, height=10, color_at=lambda t: _resource_risk_color(0.30, t))
    parts.append(f'<text x="{x + 145:.2f}" y="{y + 67:.2f}" fill="#332719" font-size="10">risk</text>')
    legend_rows = [
        ("detect", MODE_COLOR["detect"], "dot"),
        ("sample", MODE_COLOR["sample"], "dot"),
        ("drill", MODE_COLOR["drill"], "dot"),
    ]
    if show_paths:
        legend_rows.extend(
            [
                ("low_time path", PATH_COLOR["low_time"], "line"),
                ("low_energy path", PATH_COLOR["low_energy"], "line"),
                ("low_risk path", PATH_COLOR["low_risk"], "line"),
            ]
        )
    if show_solution:
        legend_rows.append(("solution", WONG_YELLOW, "line"))
    row_y = y + 91
    for label, color, kind in legend_rows:
        if kind == "line":
            parts.append(
                f'<line x1="{x + 14:.2f}" y1="{row_y - 4:.2f}" x2="{x + 43:.2f}" y2="{row_y - 4:.2f}" '
                f'stroke="{color}" stroke-width="3.0" stroke-linecap="round"/>'
            )
        else:
            parts.append(f'<circle cx="{x + 28:.2f}" cy="{row_y - 4:.2f}" r="4.2" fill="{color}" stroke="#332719" stroke-width="0.6"/>')
        parts.append(f'<text x="{x + 52:.2f}" y="{row_y:.2f}" fill="#332719" font-size="10">{label}</text>')
        row_y += 15


def _add_dem_legend(
    parts: list[str],
    *,
    x: float,
    y: float,
    show_paths: bool = False,
    show_solution: bool = False,
) -> None:
    row_count = 3 + (3 if show_paths else 0) + (1 if show_solution else 0)
    height = 76 + 15 * row_count
    parts.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="208" height="{height}" rx="5" '
        'fill="#fff2cf" opacity="0.90" stroke="#7a5a2a" stroke-width="0.8"/>'
    )
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 21:.2f}" fill="#332719" font-size="12" font-weight="700">DEM legend</text>')
    _add_colorbar(parts, x=x + 12, y=y + 36, width=132, height=11, color_at=_dem_color)
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 62:.2f}" fill="#332719" font-size="10">low basin</text>')
    parts.append(f'<text x="{x + 103:.2f}" y="{y + 62:.2f}" fill="#332719" font-size="10">high ridge</text>')
    mode_rows = [
        ("detect", MODE_COLOR["detect"], "dot"),
        ("sample", MODE_COLOR["sample"], "dot"),
        ("drill", MODE_COLOR["drill"], "dot"),
    ]
    if show_paths:
        mode_rows.extend(
            [
                ("low_time path", PATH_COLOR["low_time"], "line"),
                ("low_energy path", PATH_COLOR["low_energy"], "line"),
                ("low_risk path", PATH_COLOR["low_risk"], "line"),
            ]
        )
    if show_solution:
        mode_rows.append(("solution", WONG_YELLOW, "line"))
    row_y = y + 83
    for label, color, kind in mode_rows:
        if kind == "line":
            parts.append(
                f'<line x1="{x + 10:.2f}" y1="{row_y - 4:.2f}" x2="{x + 35:.2f}" y2="{row_y - 4:.2f}" '
                f'stroke="{color}" stroke-width="3.0" stroke-linecap="round"/>'
            )
        else:
            parts.append(f'<circle cx="{x + 19:.2f}" cy="{row_y - 4:.2f}" r="4.2" fill="{color}" stroke="#332719" stroke-width="0.6"/>')
        parts.append(f'<text x="{x + 43:.2f}" y="{row_y:.2f}" fill="#332719" font-size="10">{label}</text>')
        row_y += 15


def _add_colorbar(parts: list[str], *, x: float, y: float, width: float, height: float, color_at: Any) -> None:
    steps = 40
    step_width = width / float(steps)
    for idx in range(steps):
        value = idx / float(steps - 1)
        parts.append(
            f'<rect x="{x + idx * step_width:.2f}" y="{y:.2f}" width="{step_width + 0.2:.2f}" '
            f'height="{height:.2f}" fill="{color_at(value)}"/>'
        )
    parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="none" stroke="#332719" stroke-width="0.5"/>')


def _add_svg_scale_bar(parts: list[str], *, size: int, pad: int, extent: float) -> None:
    bar_km = 10.0 if extent >= 40.0 else 5.0
    x0 = pad + 0.06 * (size - 2 * pad)
    y0 = size - pad - 24.0
    length = bar_km / float(extent) * (size - 2 * pad)
    parts.append(f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x0 + length:.2f}" y2="{y0:.2f}" stroke="#202020" stroke-width="1.8" stroke-linecap="butt"/>')
    parts.append(f'<text x="{x0 + 0.5 * length:.2f}" y="{y0 - 8.0:.2f}" fill="#111827" stroke="#fbfbf8" stroke-width="2.5" paint-order="stroke" font-size="12" text-anchor="middle">{bar_km:.0f} km</text>')


def _blend_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    u = _clamp(t)
    return (
        int(round(a[0] + (b[0] - a[0]) * u)),
        int(round(a[1] + (b[1] - a[1]) * u)),
        int(round(a[2] + (b[2] - a[2]) * u)),
    )


def _rgb_hex(color: tuple[int, int, int]) -> str:
    return f"#{max(0, min(255, color[0])):02x}{max(0, min(255, color[1])):02x}{max(0, min(255, color[2])):02x}"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _smoothstep(value: float) -> float:
    v = _clamp(value)
    return v * v * (3.0 - 2.0 * v)

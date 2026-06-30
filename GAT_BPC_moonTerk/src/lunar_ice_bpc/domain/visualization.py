"""Dependency-free SVG visualization for lunar-ice instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lunar_ice_bpc.io.instance_io import read_json


MODE_COLOR = {"detect": "#2b83ba", "sample": "#abdda4", "drill": "#d7191c"}
PATH_COLOR = {"low_time": "#3b82f6", "low_energy": "#10b981", "low_risk": "#ef4444"}


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


def write_svg(instance_path: str | Path, output_path: str | Path, *, solution_path: str | Path | None = None) -> Path:
    instance = read_json(instance_path)
    solution = read_json(solution_path) if solution_path else instance.get("reference_solution", {})
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    size = 920
    pad = 55
    extent = float(instance["resource_map"]["extent_km"])
    preview = instance["resource_map"].get("preview", [])
    cell_count = len(preview) or 1
    cell_size = (size - 2 * pad) / float(cell_count)
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#071013"/>',
    ]
    for row, values in enumerate(preview):
        for col, value in enumerate(values):
            value = max(0.0, min(1.0, float(value)))
            blue = int(50 + 150 * value)
            green = int(45 + 70 * value)
            color = f"#{20:02x}{green:02x}{blue:02x}"
            x = pad + col * cell_size
            y = pad + row * cell_size
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size + 0.2:.2f}" height="{cell_size + 0.2:.2f}" fill="{color}"/>')
    parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="none" stroke="#d6e4e5" stroke-width="1.2"/>')
    edge_lookup = _edge_options(instance)
    tasks = instance["tasks"]
    first_tasks = list(tasks.keys())[: min(3, len(tasks))]
    for task_id in first_tasks:
        for path_type, option in edge_lookup.get(("depot", task_id), {}).items():
            points = option.get("path_xy") or [instance["depot"]["xy_km"], tasks[task_id]["xy_km"]]
            parts.append(
                f'<polyline points="{_polyline(points, extent, size, pad)}" fill="none" stroke="{PATH_COLOR[path_type]}" '
                f'stroke-width="1.4" opacity="0.55"/>'
            )
    for journey in solution.get("journeys", []):
        for sortie in journey.get("sorties", []):
            for leg in sortie.get("legs", []):
                option = edge_lookup.get((leg["from"], leg["to"]), {}).get(leg.get("path_type", "low_risk"))
                if not option:
                    continue
                parts.append(
                    f'<polyline points="{_polyline(option.get("path_xy", []), extent, size, pad)}" fill="none" '
                    f'stroke="#ffd166" stroke-width="3.0" opacity="0.85"/>'
                )
    depot_x, depot_y = _scale_xy(instance["depot"]["xy_km"][0], instance["depot"]["xy_km"][1], extent, size, pad)
    parts.append(f'<circle cx="{depot_x:.2f}" cy="{depot_y:.2f}" r="8" fill="#f9f871" stroke="#111" stroke-width="1.5"/>')
    parts.append(f'<text x="{depot_x + 10:.2f}" y="{depot_y - 10:.2f}" fill="#f8fafc" font-size="14">depot</text>')
    for task_id, task in tasks.items():
        x, y = _scale_xy(task["xy_km"][0], task["xy_km"][1], extent, size, pad)
        color = MODE_COLOR.get(task.get("operation_mode"), "#e5e7eb")
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="{color}" stroke="#0b0f10" stroke-width="1.0"/>')
    title = f'{instance["instance_id"]} | {len(tasks)} targets | status={solution.get("status", "reference")}'
    parts.append(f'<text x="{pad}" y="32" fill="#f8fafc" font-size="18" font-family="monospace">{title}</text>')
    parts.append('<text x="55" y="890" fill="#d1d5db" font-size="13">background: ice/shadow resource map; blue/green/red lines: three path options; yellow: solution overlay</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


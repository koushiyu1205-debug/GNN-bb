#!/usr/bin/env python3
"""Draw a compact TRC-style time-window table for the seven paper sites."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


INSTANCE_PATH = (
    ROOT / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
)
OUTPUT_PNG = (
    ROOT
    / "output/data_figures/"
    "lunar_sp50_020_instance_001_schematic_v5_time_windows.png"
)
OUTPUT_PDF = OUTPUT_PNG.with_suffix(".pdf")

TASK_IDS = (
    "ice_site_001",
    "ice_site_003",
    "ice_site_004",
    "ice_site_006",
    "ice_site_007",
    "ice_site_009",
    "ice_site_018",
)
TASK_MARKERS = {
    "detect": "o",
    "sample": "^",
    "drill": "s",
}
OPERATION_LABELS = {
    "detect": "Detection",
    "sample": "Sampling",
    "drill": "Drilling",
}


def main() -> int:
    instance = read_json(INSTANCE_PATH)
    tasks_by_id = instance.get("tasks") or {}
    missing = [task_id for task_id in TASK_IDS if task_id not in tasks_by_id]
    if missing:
        raise KeyError(f"missing representative tasks: {missing}")

    rows = [_build_row(tasks_by_id[task_id]) for task_id in TASK_IDS]
    horizon_min = float((instance.get("scheduling") or {})["horizon_min"])

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 450,
            "figure.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
        }
    )
    fig, ax = plt.subplots(figsize=(10.8, 4.15), facecolor="white")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    left = 0.025
    right = 0.975
    table_top = 0.955
    table_bottom = 0.185
    header_height = 0.135
    body_height = table_top - table_bottom - header_height
    row_height = body_height / len(rows)
    column_widths = (0.115, 0.135, 0.145, 0.155, 0.145, 0.305)
    x_edges = [left]
    usable_width = right - left
    for width in column_widths:
        x_edges.append(x_edges[-1] + usable_width * width)

    header_color = "#E7ECEF"
    alternate_color = "#F7F8F8"
    rule_color = "#AEB7BC"
    strong_rule_color = "#253238"
    text_color = "#172126"

    ax.add_patch(
        Rectangle(
            (left, table_top - header_height),
            right - left,
            header_height,
            facecolor=header_color,
            edgecolor="none",
            zorder=0,
        )
    )
    for row_index in range(len(rows)):
        if row_index % 2 == 1:
            row_top = table_top - header_height - row_index * row_height
            ax.add_patch(
                Rectangle(
                    (left, row_top - row_height),
                    right - left,
                    row_height,
                    facecolor=alternate_color,
                    edgecolor="none",
                    zorder=0,
                )
            )

    ax.plot(
        [left, right],
        [table_top, table_top],
        color=strong_rule_color,
        linewidth=1.25,
        zorder=2,
    )
    header_bottom = table_top - header_height
    ax.plot(
        [left, right],
        [header_bottom, header_bottom],
        color=strong_rule_color,
        linewidth=0.95,
        zorder=2,
    )
    for row_index in range(1, len(rows)):
        y = header_bottom - row_index * row_height
        ax.plot(
            [left, right],
            [y, y],
            color=rule_color,
            linewidth=0.45,
            zorder=2,
        )
    ax.plot(
        [left, right],
        [table_bottom, table_bottom],
        color=strong_rule_color,
        linewidth=1.25,
        zorder=2,
    )

    headers = (
        "Task site",
        "Operation",
        "Earliest service\nstart, $r_i$ (min)",
        "Latest service\ncompletion, $D_i$ (min)",
        "Service duration,\n$\\sigma_i$ (min)",
        "Feasible service-start interval,\n$[r_i,\\,D_i-\\sigma_i]$ (min)",
    )
    for column_index, header in enumerate(headers):
        x = 0.5 * (x_edges[column_index] + x_edges[column_index + 1])
        ax.text(
            x,
            table_top - 0.5 * header_height,
            header,
            ha="center",
            va="center",
            color=text_color,
            fontsize=8.4,
            fontweight="semibold",
            linespacing=1.18,
        )

    for row_index, row in enumerate(rows):
        row_y = header_bottom - (row_index + 0.5) * row_height
        first_center = 0.5 * (x_edges[0] + x_edges[1])
        marker_x = first_center - 0.018
        ax.scatter(
            [marker_x],
            [row_y],
            s=74,
            marker=TASK_MARKERS[row["operation_mode"]],
            facecolor="#FFE16A",
            edgecolor="#11181D",
            linewidth=0.85,
            zorder=4,
        )
        ax.text(
            first_center + 0.010,
            row_y,
            row["short_id"],
            ha="left",
            va="center",
            color=text_color,
            fontsize=8.8,
        )
        cell_values = (
            OPERATION_LABELS[row["operation_mode"]],
            f"{row['earliest_start']:.0f}",
            f"{row['latest_completion']:.0f}",
            f"{row['service_duration']:.1f}",
            (
                f"[{row['earliest_start']:.0f}, "
                f"{row['latest_start']:.1f}]"
            ),
        )
        for value_index, value in enumerate(cell_values, start=1):
            x = 0.5 * (x_edges[value_index] + x_edges[value_index + 1])
            ax.text(
                x,
                row_y,
                value,
                ha="center",
                va="center",
                color=text_color,
                fontsize=8.8,
            )

    ax.text(
        left,
        0.115,
        (
            "Note: Times are measured from the beginning of the fixed mission "
            f"horizon ($H^{{\\mathrm{{mis}}}}={horizon_min:.0f}$ min). "
            "Because waiting at task sites is prohibited, service must start "
            "within $[r_i,\\,D_i-\\sigma_i]$."
        ),
        ha="left",
        va="top",
        fontsize=8.2,
        color="#3E4A50",
    )

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "Title": "Time windows for the seven representative lunar task sites",
        "Description": (
            "Data-backed table from instance_001_logical_graph.json. The original "
            "task window is [earliest service start, latest service completion]; "
            "the derived feasible service-start interval is [r_i, D_i-sigma_i]."
        ),
        "Software": "lunar-ice-bpc deterministic Matplotlib renderer",
    }
    fig.savefig(
        OUTPUT_PNG,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
        metadata=metadata,
    )
    fig.savefig(
        OUTPUT_PDF,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
        metadata={"Title": metadata["Title"], "Subject": metadata["Description"]},
    )
    plt.close(fig)

    print(f"wrote {OUTPUT_PNG}")
    print(f"wrote {OUTPUT_PDF}")
    for row in rows:
        print(
            f"{row['task_id']} mode={row['operation_mode']} "
            f"window=[{row['earliest_start']:.1f},{row['latest_completion']:.1f}] "
            f"service={row['service_duration']:.4f} "
            f"start=[{row['earliest_start']:.1f},{row['latest_start']:.4f}]"
        )
    return 0


def _build_row(task: dict[str, Any]) -> dict[str, Any]:
    earliest_start = float(task["r"])
    latest_completion = float(task["D"])
    service_duration = float(task["sigma"])
    latest_start = latest_completion - service_duration
    if latest_start < earliest_start:
        raise ValueError(
            f"task {task.get('id')} has an empty service-start interval: "
            f"[{earliest_start}, {latest_start}]"
        )
    task_id = str(task["id"])
    operation_mode = str(task["operation_mode"])
    if operation_mode not in TASK_MARKERS:
        raise ValueError(f"unsupported task operation mode: {operation_mode}")
    return {
        "task_id": task_id,
        "short_id": task_id.removeprefix("ice_site_"),
        "operation_mode": operation_mode,
        "earliest_start": earliest_start,
        "latest_completion": latest_completion,
        "service_duration": service_duration,
        "latest_start": latest_start,
    }


if __name__ == "__main__":
    raise SystemExit(main())

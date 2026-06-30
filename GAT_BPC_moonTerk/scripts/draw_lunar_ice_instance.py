#!/usr/bin/env python3
"""Draw a lunar-ice instance as an SVG resource map."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.visualization import write_svg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--solution", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--path-preview", choices=("none", "sample", "all"), default="all")
    parser.add_argument("--background-mode", choices=("resource", "dem"), default="resource")
    parser.add_argument("--also-dem", action="store_true")
    parser.add_argument("--output-dem", default=None)
    parser.add_argument("--no-logical-edges", action="store_true")
    parser.add_argument("--show-reference-solution", action="store_true")
    parser.add_argument("--split-views", action="store_true")
    args = parser.parse_args()
    instance_path = Path(args.instance)
    if not instance_path.is_absolute():
        instance_path = ROOT / instance_path
    solution_path = Path(args.solution) if args.solution else None
    if solution_path is not None and not solution_path.is_absolute():
        solution_path = ROOT / solution_path
    output = Path(args.output) if args.output else ROOT / "runs" / "figures" / f"{instance_path.stem}.svg"
    if not output.is_absolute():
        output = ROOT / output
    if args.split_views:
        for suffix, show_edges, path_preview in (
            ("logical_graph", True, "none"),
            ("path_options", False, "all"),
            ("targets", False, "none"),
        ):
            view_output = output.with_name(f"{output.stem}_{suffix}{output.suffix}")
            path = write_svg(
                instance_path,
                view_output,
                solution_path=solution_path,
                show_logical_edges=show_edges,
                path_preview=path_preview,
                background_mode=args.background_mode,
                show_reference_solution=args.show_reference_solution,
            )
            print(f"wrote {path}")
            if args.also_dem:
                dem_output = view_output.with_name(f"{view_output.stem}_dem{view_output.suffix}")
                dem_path = write_svg(
                    instance_path,
                    dem_output,
                    solution_path=solution_path,
                    show_logical_edges=show_edges,
                    path_preview=path_preview,
                    background_mode="dem",
                    show_reference_solution=args.show_reference_solution,
                )
                print(f"wrote {dem_path}")
        return 0
    path = write_svg(
        instance_path,
        output,
        solution_path=solution_path,
        show_logical_edges=not args.no_logical_edges,
        path_preview=args.path_preview,
        background_mode=args.background_mode,
        show_reference_solution=args.show_reference_solution,
    )
    print(f"wrote {path}")
    if args.also_dem:
        dem_output = Path(args.output_dem) if args.output_dem else output.with_name(f"{output.stem}_dem{output.suffix}")
        if not dem_output.is_absolute():
            dem_output = ROOT / dem_output
        dem_path = write_svg(
            instance_path,
            dem_output,
            solution_path=solution_path,
            show_logical_edges=not args.no_logical_edges,
            path_preview=args.path_preview,
            background_mode="dem",
            show_reference_solution=args.show_reference_solution,
        )
        print(f"wrote {dem_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

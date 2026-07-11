#!/usr/bin/env python3
"""Run cold-start diagnostic rows for BPC labeling worker pricing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.labeling_worker_diagnostic import (  # noqa: E402
    DEFAULT_WORKERS,
    run_labeling_worker_diagnostic,
    write_labeling_worker_diagnostic_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", action="append", default=[], help="Instance JSON path. May be repeated.")
    parser.add_argument("--scale", action="append", type=int, default=[], help="Load data/instances/lunar_ice_sp50_<scale>.")
    parser.add_argument("--limit", type=int, default=0, help="Limit instances per scale after sorting.")
    parser.add_argument("--worker", action="append", default=[], help="direct_label or relaxed_labeling. May be repeated.")
    parser.add_argument("--max-rounds", type=int, default=1)
    parser.add_argument("--max-columns-per-round", type=int, default=16)
    parser.add_argument("--row-time-limit-sec", type=float, default=30.0)
    parser.add_argument("--tail-dual-stabilization-enabled", action="store_true")
    parser.add_argument("--tail-dual-stabilization-alpha", type=float, default=0.7)
    parser.add_argument("--tail-dual-stabilization-window", type=int, default=5)
    parser.add_argument(
        "--rows-csv",
        default="runs/labeling_worker_diagnostic/labeling_worker_rows.csv",
    )
    parser.add_argument(
        "--summary-json",
        default="runs/labeling_worker_diagnostic/labeling_worker_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="runs/labeling_worker_diagnostic/labeling_worker_report_zh.md",
    )
    args = parser.parse_args()

    instance_paths = _instance_paths(args)
    if not instance_paths:
        parser.error("provide --instance or --scale")

    report = run_labeling_worker_diagnostic(
        instance_paths,
        project_root=ROOT,
        workers=tuple(args.worker) if args.worker else DEFAULT_WORKERS,
        max_rounds=args.max_rounds,
        max_columns_per_round=args.max_columns_per_round,
        row_time_limit_sec=args.row_time_limit_sec,
        tail_dual_stabilization_enabled=args.tail_dual_stabilization_enabled,
        tail_dual_stabilization_alpha=args.tail_dual_stabilization_alpha,
        tail_dual_stabilization_window=args.tail_dual_stabilization_window,
    )
    write_labeling_worker_diagnostic_artifacts(
        report,
        rows_csv=ROOT / args.rows_csv,
        summary_json=ROOT / args.summary_json,
        report_md=ROOT / args.report_md,
    )
    print(
        "ran {rows} labeling-worker diagnostic rows; report={report}".format(
            rows=report["row_count"],
            report=args.report_md,
        )
    )
    return 0


def _instance_paths(args: argparse.Namespace) -> tuple[Path, ...]:
    rows: list[Path] = []
    for value in args.instance:
        path = Path(value)
        rows.append(path if path.is_absolute() else ROOT / path)
    for scale in args.scale:
        scale_dir = ROOT / "data" / "instances" / f"lunar_ice_sp50_{int(scale):03d}"
        found = sorted(scale_dir.glob("instance_*_logical_graph.json"))
        if args.limit:
            found = found[: max(0, int(args.limit))]
        rows.extend(found)
    seen = set()
    deduped: list[Path] = []
    for path in rows:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return tuple(deduped)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run B0/B1 proof-safe ablation matrix."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.b0_b1_ablation import (  # noqa: E402
    run_b0_b1_ablation_matrix,
    write_b0_b1_ablation_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifests/lunar_ice_sp50_real_benchmark_manifest.json")
    parser.add_argument("--rows-csv", default="runs/b0_b1_ablation/b0_b1_ablation_rows.csv")
    parser.add_argument("--summary-json", default="runs/b0_b1_ablation/b0_b1_ablation_summary.json")
    parser.add_argument("--report-md", default="runs/b0_b1_ablation/b0_b1_ablation_report_zh.md")
    parser.add_argument("--scale10-limit", type=int, default=5)
    parser.add_argument("--scale10-row-time-limit", type=float, default=60.0)
    parser.add_argument("--scale20-probe-limit", type=int, default=1)
    parser.add_argument("--direct20-probe-time-limit", type=float, default=60.0)
    parser.add_argument("--fail-closed-max-direct-tasks", type=int, default=10)
    parser.add_argument("--b1-max-rounds", type=int, default=8)
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args()

    report = run_b0_b1_ablation_matrix(
        manifest_path=args.manifest,
        project_root=ROOT,
        scale10_limit=args.scale10_limit,
        scale10_row_time_limit_sec=args.scale10_row_time_limit,
        scale20_probe_limit=args.scale20_probe_limit,
        direct20_probe_time_limit_sec=args.direct20_probe_time_limit,
        fail_closed_max_direct_tasks=args.fail_closed_max_direct_tasks,
        b1_max_rounds=args.b1_max_rounds,
        max_workers=args.max_workers,
    )
    write_b0_b1_ablation_artifacts(
        report,
        rows_csv=ROOT / args.rows_csv,
        summary_json=ROOT / args.summary_json,
        report_md=ROOT / args.report_md,
    )
    redlines = report["redlines"]
    print(
        "ran {row_count} B0/B1 ablation rows; redlines={redlines}; csv={csv}; report={report}".format(
            row_count=report["row_count"],
            redlines=redlines,
            csv=args.rows_csv,
            report=args.report_md,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

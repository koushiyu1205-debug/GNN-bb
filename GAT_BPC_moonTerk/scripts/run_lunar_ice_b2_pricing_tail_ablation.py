#!/usr/bin/env python3
"""Run B2 pricing-tail proof-safe ablation matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.b2_pricing_tail_ablation import (  # noqa: E402
    merge_b2_pricing_tail_reports,
    run_b2_pricing_tail_b2b_r2_direct20_probe,
    run_b2_pricing_tail_b2b_r2_incremental,
    run_b2_pricing_tail_direct20_probe,
    run_b2_pricing_tail_ablation_matrix,
    write_b2_pricing_tail_ablation_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifests/lunar_ice_sp50_real_benchmark_manifest.json")
    parser.add_argument("--rows-csv", default="runs/b2_pricing_tail_ablation/b2_pricing_tail_rows.csv")
    parser.add_argument("--summary-json", default="runs/b2_pricing_tail_ablation/b2_pricing_tail_summary.json")
    parser.add_argument("--report-md", default="runs/b2_pricing_tail_ablation/b2_pricing_tail_report_zh.md")
    parser.add_argument("--scale10-limit", type=int, default=5)
    parser.add_argument("--scale10-row-time-limit", type=float, default=30.0)
    parser.add_argument("--scale20-probe-limit", type=int, default=5)
    parser.add_argument("--scale20-probe-offset", type=int, default=0)
    parser.add_argument("--direct20-probe-time-limit", type=float, default=120.0)
    parser.add_argument("--fail-closed-max-direct-tasks", type=int, default=10)
    parser.add_argument("--b1-max-rounds", type=int, default=8)
    parser.add_argument("--b2-max-rounds", type=int, default=8)
    parser.add_argument(
        "--direct20-only",
        action="store_true",
        help="Run only the 20-scale selected direct20 probe rows.",
    )
    parser.add_argument(
        "--b2b-r2-only",
        action="store_true",
        help="Run only B2B_R2 rows for the B2 matrix groups.",
    )
    parser.add_argument(
        "--b2b-r2-direct20-only",
        action="store_true",
        help="Run only B2B_R2 rows for the 20-scale selected direct20 probe.",
    )
    parser.add_argument(
        "--merge-existing-summary",
        action="store_true",
        help="With an *-only mode, merge rows into the existing --summary-json artifact.",
    )
    args = parser.parse_args()

    only_modes = [args.direct20_only, args.b2b_r2_only, args.b2b_r2_direct20_only]
    if sum(bool(value) for value in only_modes) > 1:
        raise SystemExit("--direct20-only, --b2b-r2-only, and --b2b-r2-direct20-only are mutually exclusive")

    if args.direct20_only:
        report = run_b2_pricing_tail_direct20_probe(
            manifest_path=args.manifest,
            project_root=ROOT,
            scale20_probe_limit=args.scale20_probe_limit,
            scale20_probe_offset=args.scale20_probe_offset,
            direct20_probe_time_limit_sec=args.direct20_probe_time_limit,
            b1_max_rounds=args.b1_max_rounds,
            b2_max_rounds=args.b2_max_rounds,
        )
        existing_summary = ROOT / args.summary_json
        if args.merge_existing_summary and existing_summary.exists():
            base_report = json.loads(existing_summary.read_text(encoding="utf-8"))
            report = merge_b2_pricing_tail_reports(base_report, report)
    elif args.b2b_r2_direct20_only:
        report = run_b2_pricing_tail_b2b_r2_direct20_probe(
            manifest_path=args.manifest,
            project_root=ROOT,
            scale20_probe_limit=args.scale20_probe_limit,
            scale20_probe_offset=args.scale20_probe_offset,
            direct20_probe_time_limit_sec=args.direct20_probe_time_limit,
            b2_max_rounds=args.b2_max_rounds,
        )
        existing_summary = ROOT / args.summary_json
        if args.merge_existing_summary and existing_summary.exists():
            base_report = json.loads(existing_summary.read_text(encoding="utf-8"))
            report = merge_b2_pricing_tail_reports(base_report, report)
    elif args.b2b_r2_only:
        report = run_b2_pricing_tail_b2b_r2_incremental(
            manifest_path=args.manifest,
            project_root=ROOT,
            scale10_limit=args.scale10_limit,
            scale10_row_time_limit_sec=args.scale10_row_time_limit,
            scale20_probe_limit=args.scale20_probe_limit,
            scale20_probe_offset=args.scale20_probe_offset,
            direct20_probe_time_limit_sec=args.direct20_probe_time_limit,
            fail_closed_max_direct_tasks=args.fail_closed_max_direct_tasks,
            b2_max_rounds=args.b2_max_rounds,
        )
        existing_summary = ROOT / args.summary_json
        if args.merge_existing_summary and existing_summary.exists():
            base_report = json.loads(existing_summary.read_text(encoding="utf-8"))
            report = merge_b2_pricing_tail_reports(base_report, report)
    else:
        report = run_b2_pricing_tail_ablation_matrix(
            manifest_path=args.manifest,
            project_root=ROOT,
            scale10_limit=args.scale10_limit,
            scale10_row_time_limit_sec=args.scale10_row_time_limit,
            scale20_probe_limit=args.scale20_probe_limit,
            direct20_probe_time_limit_sec=args.direct20_probe_time_limit,
            fail_closed_max_direct_tasks=args.fail_closed_max_direct_tasks,
            b1_max_rounds=args.b1_max_rounds,
            b2_max_rounds=args.b2_max_rounds,
        )
    write_b2_pricing_tail_ablation_artifacts(
        report,
        rows_csv=ROOT / args.rows_csv,
        summary_json=ROOT / args.summary_json,
        report_md=ROOT / args.report_md,
    )
    print(
        "ran {row_count} B2 pricing-tail ablation rows; redlines={redlines}; accepted={accepted}; report={report}".format(
            row_count=report["row_count"],
            redlines=report["redlines"],
            accepted=report["acceptance"]["b2_accepted"],
            report=args.report_md,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
